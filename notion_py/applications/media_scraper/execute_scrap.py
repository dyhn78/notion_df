import re
from pprint import pprint

from ...interface import RootEditor, TypeName
from ..page_ids import DatabaseInfo
from .lib_entry import LibraryScraper
from .yes24_entry import Yes24Scraper
from .property_frame import reading_database_frame
from ...interface.utility import stopwatch


class ReadingDBEditor:
    def __init__(self):
        self.root_editor = RootEditor()
        self.frame = reading_database_frame
        self.database = RootEditor().open_database(
            *DatabaseInfo.READINGS, self.frame)
        self.pagelist = self.database.pagelist
        self.status_enum = self.frame.by_key['edit_status'].values


class MediaScraper(ReadingDBEditor):
    def __init__(self, targets=None):
        super().__init__()
        if targets is None:
            # targets = {'yes24', 'gy_lib', 'snu_lib'}
            targets = {'yes24'}
        self.targets = targets

    def execute(self, page_size=0):
        self.make_query()
        self.pagelist.run_query(page_size)
        for page in self.pagelist:
            page.children.fetch()
            unit = PageHandler(self, page)
            unit.execute()
            # pprint(page.preview())
            page.execute()
            unit.set_edit_status()
            page.execute()

    def make_query(self):
        query = self.pagelist.query_form
        maker = query.make_filter.select_at('media_type')
        ft_media = maker.equals_to_any(maker.value_groups['book'])
        maker = query.make_filter.select_at('edit_status')
        ft_status = maker.equals_to_any(maker.value_groups['regulars'])
        ft_status |= maker.is_empty()
        query.push_filter(ft_media & ft_status)


class PageHandler:
    def __init__(self, caller: MediaScraper, page: TypeName.tabular_page):
        self.caller = caller
        self.frame = caller.frame
        self.targets = caller.targets.copy()
        self.status_enum = caller.status_enum

        self.page = page
        self.props = page.props
        self.children = page.children
        self.status = ''
        self.rich_overwrite_option = self.get_overwrite_option()
        if self.rich_overwrite_option == 'continue':
            self.targets.remove('yes24')

    def execute(self):
        if not self.targets:
            return
        stopwatch(f'개시: {self.page.title}')
        if 'yes24' in self.targets:
            yes24 = Yes24Scraper(self)
            yes24.execute()
        if any(lib in self.targets for lib in ['snu_lib', 'gy_lib']):
            lib = LibraryScraper(self)
            lib.execute()

    def set_overwrite_option(self, option: bool):
        if option:
            self.props.set_overwrite_option(True)
        else:
            if self.rich_overwrite_option in ['append', 'continue']:
                self.props.set_overwrite_option(False)
            elif self.rich_overwrite_option == ['overwrite']:
                self.props.set_overwrite_option(True)

    def set_edit_status(self):
        if not self.status:
            if self.rich_overwrite_option == 'append':
                self.status = self.status_enum['done']
            elif self.rich_overwrite_option == 'continue':
                self.status = self.status_enum['done']
            elif self.rich_overwrite_option == 'overwrite':
                self.status = self.status_enum['completely_done']
        self.set_overwrite_option(True)
        self.props.write_select_at('edit_status', self.status)
        self.set_overwrite_option(False)

    def get_overwrite_option(self):
        edit_status = self.props.read_at('edit_status')
        try:
            charref = re.compile(r'(?<=\().+(?=\))')
            return re.findall(charref, edit_status)[0]
        except (TypeError,  # read() 가 keyError로 edit_status를 반환할 경우
                IndexError):  # findall() 가 빈 리스트를 반환할 경우
            return 'append'

    def get_names(self) -> tuple[str, str]:
        docx_name = self.props.read_at('docx_name', '')
        true_name = self.props.read_at('true_name', '')
        return docx_name, true_name

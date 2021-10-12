import re
from typing import Optional

from notion_py.applications.media_scraper.common.editor import ReadingDBEditor
from notion_py.applications.media_scraper.lib import LibraryScraper
from notion_py.applications.media_scraper.bookstore import BookstoreScraper
from notion_py.interface.utility import stopwatch
from notion_py.interface.editor.tabular import TabularPageBlock


class ReadingDBRegularScraper(ReadingDBEditor):
    def __init__(self, targets: Optional[dict] = None, title=''):
        super().__init__()
        if not targets:
            targets = {'bookstore', 'gy_lib', 'snu_lib'}
        self.targets = targets
        self.title = title

    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist:
            page.sphere.fetch_children()
            unit = PageHandler(self, page)
            unit.execute()

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.make_filter.select_at('media_type')
        ft_media = maker.equals_to_any(maker.prop_value_groups['book'])
        maker = query.make_filter.select_at('edit_status')
        ft_status = maker.equals_to_any(maker.prop_value_groups['regulars'])
        ft_status |= maker.is_empty()
        ft = ft_media & ft_status
        if self.title:
            maker = query.make_filter.text_at('title')
            ft_title = maker.equals(self.title)
            ft &= ft_title
        query.push_filter(ft)
        query.execute(request_size)


class PageHandler:
    def __init__(self, caller: ReadingDBRegularScraper, page: TabularPageBlock):
        self.caller = caller
        self.frame = caller.frame
        self.targets = caller.targets.copy()
        self.status_enum = caller.status_enum

        self.page = page
        self.props = page.props
        self.sphere = page.sphere
        self.status = ''
        self.rich_overwrite_option = self.get_overwrite_option()
        if self.rich_overwrite_option == 'continue':
            self.targets.remove('bookstore')

    def execute(self):
        if not self.targets:
            return
        stopwatch(f'개시: {self.page.title}')
        if 'bookstore' in self.targets:
            bkst = BookstoreScraper(self)
            bkst.execute()
        if any(lib in self.targets for lib in ['snu_lib', 'gy_lib']):
            lib = LibraryScraper(self)
            lib.execute()
        self.set_edit_status()
        self.page.execute()

    def set_overwrite_option(self, option: bool):
        if option:
            self.props.set_overwrite_option(True)
        else:
            if self.rich_overwrite_option in ['append', 'continue']:
                self.props.set_overwrite_option(False)
            elif self.rich_overwrite_option == ['overwrite']:
                pass

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
        docx_name = self.props.try_read_at('docx_name', '')
        true_name = self.props.try_read_at('true_name', '')
        return docx_name, true_name

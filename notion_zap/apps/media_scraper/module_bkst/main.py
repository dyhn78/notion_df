from notion_zap.cli import editors
from notion_zap.cli.utility import stopwatch
from .yes24_main import scrap_yes24_main
from .yes24_url import scrap_yes24_url
from ..common.helpers import enumerate_func
from ..common.insert_contents_data import InsertContents
from ..common.remove_dummy_blocks import remove_dummy_blocks
from ..structs.controller_base_logic import ReadingPageWriter
from ..structs.exceptions import NoURLFoundError


class BookstoreManager:
    pass
    # TODO: module_lib.writer.py 참고해서 비슷하게
    #  "Scrapers' Manager" 와 "Writing Agent" 의 역할 분리.


class BookstoreDataWriter:
    def __init__(self, status: ReadingPageWriter):
        self.status = status
        self.page = self.status.page
        self.book_names = self.status.book_names

    def execute(self):
        try:
            url = self.read_or_scrap_url()
            if not url:
                raise NoURLFoundError
            data = self.scrap_bkst_data(url)
            if not data:
                raise NoURLFoundError
        except NoURLFoundError:
            self.status.set_url_missing_flag()
        else:
            self.set_metadata(data)
            self.set_cover_image(data)
            self.set_contents_data(data)

    def read_or_scrap_url(self):
        if url := self.page.props.get_tag('url', default=''):
            return url
        if url := enumerate_func(scrap_yes24_url)(self.book_names):
            self.page.props.write_url_at('url', url)
            return url
        return ''

    @staticmethod
    def scrap_bkst_data(url):
        if 'yes24' in url:
            data = scrap_yes24_main(url)
            stopwatch(f'yes24: {url}')
            return data
        if 'aladin' in url:
            pass

    def set_metadata(self, data: dict):
        if self.status.can_disable_overwrite:
            self.page.root.disable_overwrite = True

        if true_name := data.get('name'):
            self.page.props.write_text_at('true_name', true_name)
        if subname := data.get('subname'):
            self.page.props.write_text_at('subname', subname)
        if author := data.get('author'):
            self.page.props.write_text_at('author', author)
        if publisher := data.get('publisher'):
            self.page.props.write_text_at('publisher', publisher)
        if volume := data.get('page_count'):
            self.page.props.write_number_at('volume', volume)
        self.page.root.disable_overwrite = False

    def set_cover_image(self, data: dict):
        if cover_image := data.get('cover_image'):
            true_name = data['name']
            file_writer = self.page.props.write_files_at('cover_image')
            file_writer.add_file(file_name=true_name,
                                 file_url=cover_image)

    def set_contents_data(self, data: dict):
        contents = data.get('contents', [])
        subpage = self.get_subpage()
        remove_dummy_blocks(subpage)
        InsertContents(subpage, contents).execute()
        link_to_contents = self.page.props.write_rich_text_at('link_to_contents')
        link_to_contents.mention_page(subpage.block_id)

    def get_subpage(self) -> editors.PageItem:
        self.page.items.fetch()
        for block in self.page.items:
            if (
                    isinstance(block, editors.PageItem)
                    and (self.page.title in block.title
                         or block.title == '=')
            ):
                subpage = block
                break
        else:
            subpage = self.page.items.create_page()
        subpage.contents.write_title(f'={self.page.title}')
        subpage.save()
        return subpage

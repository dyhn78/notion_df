from notion_py.interface.editor.inline import PageItem
from notion_py.interface.utility import stopwatch
from .contents_append import AppendContents
from .yes24_main import scrap_yes24_main
from .yes24_url import scrap_yes24_url
from ..regular_scrap import ReadingDBScrapController, ReadingPageScrapController
from ..remove_duplicates import remove_dummy_blocks


class BookstoreScrapManager:
    # TODO : yes24에 자료 없을 경우 대비해 알라딘 등 추가 필요.
    def __init__(self, caller: ReadingDBScrapController):
        self.caller = caller
        self.subpage_id = ''
        self.data = {}

    def execute(self, page_cont: ReadingPageScrapController):
        scraper = BookstoreScraper(self, page_cont)
        scraper.execute()


class BookstoreScraper:
    def __init__(self, caller: BookstoreScrapManager,
                 page_cont: ReadingPageScrapController):
        self.caller = caller
        self.cont = page_cont
        self.page = self.cont.page

    def execute(self):
        try:
            self._execute_naive()
        except ValueError:
            self.cont.set_as_url_missing()

    def _execute_naive(self):
        url = self.get_or_scrap_url()
        if not url:
            raise ValueError
        data = self.scrap_bkst_data(url)
        if not data:
            raise ValueError
        self.set_metadata(data)
        self.set_cover_image(data)
        self.set_contents_data(data)

    def get_or_scrap_url(self):
        if url := self.page.props.get_at('url', default=''):
            return url
        if url := scrap_yes24_url(self.cont.get_names()):
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
        if self.cont.can_disable_overwrite:
            self.page.root.enable_overwrite = False

        if true_name := data.get('name'):
            self.page.props.write_text_at('true_name', true_name)
        if subname := data.get('subname'):
            self.page.props.write_text_at('subname', subname)
        if author := data.get('author'):
            self.page.props.write_text_at('author', author)
        if publisher := data.get('publisher'):
            self.page.props.write_text_at('publisher', publisher)
        if volume := data.get('page_count'):
            self.page.props.write_text_at('volume', volume)

        self.page.root.enable_overwrite = True

    def set_cover_image(self, data: dict):
        if cover_image := data.get('cover_image'):
            true_name = data['name']
            file_writer = self.page.props.write_files_at('cover_image')
            file_writer.add_file(file_name=true_name,
                                 file_url=cover_image)

    def set_contents_data(self, data: dict):
        contents = data['contents']
        subpage = self.get_subpage()
        remove_dummy_blocks(subpage)
        AppendContents(subpage, contents).execute()
        writer = self.page.props.write_rich_text_at('link_to_contents')
        writer.mention_page(subpage.master_id)

    def get_subpage(self) -> PageItem:
        self.page.attachments.fetch_children()
        for block in self.page.attachments:
            if isinstance(block, PageItem) and \
                    self.page.title in block.contents.reads():
                subpage = block
                # print(block.master_name)
                # print(block.master_url)
                # print(f"<{block.master_id}>")
                # continue
                break
        else:
            subpage = self.page.attachments.create_page_item()
        subpage.contents.write_title(f'={self.page.title}')
        subpage.save()
        return subpage

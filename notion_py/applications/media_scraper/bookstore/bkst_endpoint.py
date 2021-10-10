from .contents_append import AppendContents
from .yes24_url import scrap_yes24_url
from .yes24_main import scrap_yes24_main
from notion_py.interface import TypeName
from notion_py.interface.utility import stopwatch
from notion_py.applications.media_scraper.remove_duplicates import remove_dummy_blocks


class BookstoreScraper:
    # TODO : yes24에 자료 없을 경우 대비해 알라딘 등 추가 필요.
    def __init__(self, handler):
        self.handler = handler
        self.page: TypeName.tabular_page = handler.page
        self.props = self.page.props
        self.sphere = self.page.sphere
        self.subpage_id = ''
        self.data = {}

    def execute(self):
        url = self.get_url()
        if not url:
            url = scrap_yes24_url(self.handler.get_names())
            self.set_url(url)
        if 'yes24' in url:
            self.data = scrap_yes24_main(url)
            stopwatch(f'yes24: {url}')
        elif 'aladin' in url:
            pass
        if self.data:
            self.set_metadata()
            self.set_contents_data()

    def get_url(self):
        url = self.props.try_read_at('url', default='')
        return url

    def set_url(self, url):
        if url:
            self.props.write_url_at('url', url)
        else:
            self.handler.status = self.handler.status_enum['url_missing']

    def set_metadata(self):
        self.handler.set_overwrite_option(False)
        self.props.write_text_at('true_name', self.data['name'])
        self.props.write_text_at('subname', self.data['subname'])
        self.props.write_text_at('author', self.data['author'])
        self.props.write_text_at('publisher', self.data['publisher'])

    def set_cover_image(self):
        file_writer = self.props.write_files_at('cover_image')
        file_writer.add_file(file_name=self.data['name'],
                             file_url=self.data['cover_image'])

    def set_contents_data(self):
        contents = self.data['contents']
        subpage = self.get_subpage()
        remove_dummy_blocks(subpage)
        AppendContents(subpage, contents).execute()
        writer = self.props.write_rich_text_at('link_to_contents')
        writer.mention_page(subpage.master_id)

    def get_subpage(self) -> TypeName.inline_page:
        for block in self.sphere.children:
            if isinstance(block, TypeName.inline_page) and \
                    self.page.title in block.contents.read():
                subpage = block
                # print(block.master_name)
                # print(block.master_url)
                # print(f"<{block.master_id}>")
                # continue
                break
        else:
            subpage = self.sphere.create_page_block()
        subpage.contents.write_title(f'={self.page.title}')
        # subpage.execute()
        return subpage

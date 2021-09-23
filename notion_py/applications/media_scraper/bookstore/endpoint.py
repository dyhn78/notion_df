from .contents_append import AppendContents
from .yes24_url import scrap_yes24_url
from .yes24_metadata import scrap_yes24_metadata
from notion_py.interface import TypeName
from notion_py.interface.utility import stopwatch


class BookstoreScraper:
    # TODO : yes24에 자료 없을 경우 대비해 알라딘 등 추가 필요.
    def __init__(self, handler):
        self.handler = handler
        self.page: TypeName.tabular_page = handler.page
        self.props = self.page.props
        self.sphere = self.page.sphere
        self.subpage_id = ''

    def execute(self):
        # pprint(self.props.read_full_of_all())
        url = self.get_url()
        if not url:
            url = scrap_yes24_url(self.handler.get_names())
            self.set_url(url)
        if url:
            if 'bookstore' in self.handler.targets:
                metadata = scrap_yes24_metadata(url)
                contents = self.set_metadata(metadata)
                self.set_contents_data(contents)
            stopwatch(f'bookstore: {url}')

    def get_url(self):
        url = self.props.read_at('url', default='')
        if 'bookstore' in url:
            return url
        else:
            return ''

    def set_url(self, url):
        if url:
            self.props.write_url_at('url', url)
        else:
            self.handler.status = self.handler.status_enum['url_missing']

    def set_metadata(self, metadata: dict):
        self.handler.set_overwrite_option(False)
        self.props.write_text_at('true_name', metadata['name'])
        self.props.write_text_at('subname', metadata['subname'])
        self.props.write_text_at('author', metadata['author'])
        self.props.write_text_at('publisher', metadata['publisher'])
        self.props.write_files_at('cover_image', 'cover_image')
        return metadata['contents']

    def set_contents_data(self, contents: list[str]):
        subpage = self.get_subpage()
        AppendContents(subpage, contents).execute()
        writer = self.props.write_rich_text_at('link_to_contents')
        writer.mention_page(subpage.master_id)

    def get_subpage(self) -> TypeName.inline_page:
        for block in self.sphere.children:
            if isinstance(block, TypeName.inline_page) and \
                    self.page.title in block.contents.read():
                block.contents.write_title(f'={self.page.title}')
                break
        else:
            block = self.sphere.create_inline_page()
            block.contents.write_title(f'={self.page.title}')
            block.execute()
        return block

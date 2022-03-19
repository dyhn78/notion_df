from notion_zap.cli import editors
from notion_zap.cli.editors import PageItem
from notion_zap.cli.utility import stopwatch
from .yes24_main import scrap_yes24_main
from .yes24_url import scrap_yes24_url
from notion_zap.apps.media_scraper.struct import ReadingPageManager
from notion_zap.apps.media_scraper.metadata.write_contents import ContentsWriter
from notion_zap.apps.media_scraper.metadata.adjust_contents import remove_dummy_blocks


class MetadataScrapManager:
    def __init__(self, targets: set[str]):
        self.targets = targets

    def __call__(self, manager: ReadingPageManager):
        writer = SubpageEditor(manager)
        writer.adjust_subpage()
        if manager.is_book:
            bkst = BookstoreWriter(manager, writer.subpage)
            if bkst.get_url():
                if bkst.scrap_data():
                    bkst.set_data()
            else:
                manager.mark_exception('no_meta_url')
        else:
            manager.mark_exception('fill_manually')

    def quit(self):
        pass


class SubpageEditor:
    def __init__(self, manager: ReadingPageManager):
        self.manager = manager
        self.page = manager.page
        self.subpage = self._get_subpage()
        self.url = ''
        self.data = {}

    def adjust_subpage(self):
        remove_dummy_blocks(self.subpage)
        if self.subpage.block_id and self.manager.enable_overwrite:
            for child in self.subpage.children:
                child.archive()
        link_to_contents = self.page.write_rich_text(key_alias='link_to_contents')
        link_to_contents.mention_page(self.subpage.block_id)
        return self.subpage

    def _get_subpage(self) -> editors.PageItem:
        self.page.items.fetch()
        for block in self.page.items:
            if (
                    isinstance(block, editors.PageItem)
                    and (self.page.title in block.title
                         or block.title.strip() in ['', '='])
            ):
                subpage = block
                break
        else:
            subpage = self.page.items.open_new_page()
        if subpage.title != f'={self.page.title}':
            subpage.write_title(f'={self.page.title}')
        subpage.save()
        return subpage


class BookstoreWriter:
    def __init__(self, manager: ReadingPageManager, subpage: PageItem):
        self.editor = manager
        self.page = manager.page
        self.titles = manager.titles
        self.write_contents = ContentsWriter()
        self.subpage = subpage
        self.url = ''
        self.data = {}

    def get_url(self):
        """return True if successfully get url."""
        if url := self.page.get_tag('url', default=''):
            self.url = url
            return True
        for title in self.titles:
            if url := scrap_yes24_url(title):
                self.page.write_url(key_alias='url', value=url)
                self.url = url
                return True
        return False

    def scrap_data(self):
        """return True if successfully get metadata."""
        if 'yes24' in self.url:
            if data := scrap_yes24_main(self.url):
                self.data = data
                stopwatch(f'yes24: {self.url}')
                return True
        if 'aladin' in self.url:
            pass
        return False

    def set_data(self):
        self.page.root.disable_overwrite = not self.editor.enable_overwrite

        if true_name := self.data.get('name'):
            self.page.write_text(key_alias='true_name', value=true_name)
        if subname := self.data.get('subname'):
            self.page.write_text(key_alias='subname', value=subname)
        if author := self.data.get('author'):
            self.page.write_text(key_alias='author', value=author)
        if publisher := self.data.get('publisher'):
            self.page.write_text(key_alias='publisher', value=publisher)
        if volume := self.data.get('page_count'):
            self.page.write_number(key_alias='volume', value=volume)

        if cover_image := self.data.get('cover_image'):
            true_name = self.data['name']
            file_writer = self.page.write_files(key_alias='cover_image')
            file_writer.add_file(file_name=true_name,
                                 file_url=cover_image)

        self.page.root.disable_overwrite = False

        contents = self.data.get('contents', [])
        self.write_contents(self.subpage, contents)

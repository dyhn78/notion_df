from notion_zap.cli import editors
from notion_zap.cli.utility import stopwatch
from .yes24_main import scrap_yes24_main
from .yes24_url import scrap_yes24_url
from ..common.struct import ReadingPageChecker
from ..common.write_contents import ContentsWriter
from ..common.remove_dummy_blocks import remove_dummy_blocks


class MetadataManager:
    def __init__(self, global_tasks: set[str]):
        self.global_tasks = global_tasks

    def __call__(self, checker: ReadingPageChecker):
        if checker.is_book:
            writer = BookstoreAgent(checker)
            writer.adjust_subpage()
            if writer.get_url():
                if writer.scrap_data():
                    writer.set_data()
            else:
                checker.mark_as_url_missing()
        else:
            writer = MetadataAgent(checker)
            writer.adjust_subpage()
            checker.mark_as_manually_filled()


# TODO
class MetadataAgent:
    def __init__(self, checker: ReadingPageChecker):
        self.checker = checker
        self.page = checker.page
        self.book_names = checker.names
        self.write_contents = ContentsWriter()
        self.subpage = self._get_subpage()
        self.url = ''
        self.data = {}

    def set_data(self):
        self.page.root.disable_overwrite = self.checker.cannot_overwrite_metadata

        if true_name := self.data.get('name'):
            self.page.write_text(tag='true_name', value=true_name)
        if subname := self.data.get('subname'):
            self.page.write_text(tag='subname', value=subname)
        if author := self.data.get('author'):
            self.page.write_text(tag='author', value=author)
        if publisher := self.data.get('publisher'):
            self.page.write_text(tag='publisher', value=publisher)
        if volume := self.data.get('page_count'):
            self.page.write_number(tag='volume', value=volume)

        if cover_image := self.data.get('cover_image'):
            true_name = self.data['name']
            file_writer = self.page.write_files(tag='cover_image')
            file_writer.add_file(file_name=true_name,
                                 file_url=cover_image)

        self.page.root.disable_overwrite = False

        contents = self.data.get('contents', [])
        self.write_contents(self.subpage, contents)

    def adjust_subpage(self):
        remove_dummy_blocks(self.subpage)
        if self.subpage.block_id and self.checker.must_clear_previous_contents:
            for child in self.subpage.children:
                child.archive()
        link_to_contents = self.page.write_rich_text(tag='link_to_contents')
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


class BookstoreAgent(MetadataAgent):
    def get_url(self):
        """return True if successfully get url."""
        if url := self.page.get_tag('url', default=''):
            self.url = url
            return True
        for name in self.book_names:
            if url := scrap_yes24_url(name):
                self.page.write_url(tag='url', value=url)
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

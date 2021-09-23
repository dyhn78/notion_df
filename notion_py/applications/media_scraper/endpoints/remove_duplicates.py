from .regular_scrap import ReadingDBEditor
from notion_py.interface import TypeName, stopwatch


class DuplicateRemover(ReadingDBEditor):
    def execute(self):
        self.pagelist.run_query()
        for page in self.pagelist.elements:
            self.edit(page)

    @staticmethod
    def edit(page: TypeName.tabular_page):
        duplicate = False
        removed = 0
        for block in page.sphere.children:
            if isinstance(block, TypeName.inline_page) and \
                    page.title in block.contents.read():
                if duplicate:
                    block.contents.archive()
                    removed += 1
                else:
                    duplicate = True
        if removed:
            page.props.write_text_at('link_to_contents', '')
            stopwatch(f'중복 {removed} 개 제거: {page.title}')
        page.execute()

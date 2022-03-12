from typing import Union

from .lib_struct import LibraryScrapResult
from ..struct import ReadingPageEditor
from .aggregate import LibraryScraperAggregate


class LibraryScrapManager:
    def __init__(self, targets: set[str], create_window=False):
        self.scrap = LibraryScraperAggregate(targets, create_window)

    def __call__(self, editor: ReadingPageEditor):
        results = self.scrap(*editor.titles)
        write_data(editor, results)

    def quit(self):
        self.scrap.quit_drivers()


def write_data(editor: ReadingPageEditor, results: dict[str, LibraryScrapResult]):
    page = editor.page
    if results:
        location, available = parse_scrap_results(results)
        page.write_text(tag='location', value=location)
        page.write_checkbox(tag='not_available', value=not available)
    else:
        if not page.read_tag('location'):
            editor.mark_as_lib_missing()


def parse_scrap_results(results: dict[str, LibraryScrapResult]):
    values = list(results.values())
    values.sort(reverse=True)
    available = values[0].available
    locations = ' '.join([str(value) for value in values if str(value)])
    return locations, available

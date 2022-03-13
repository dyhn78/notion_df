from notion_zap.apps.externals.selenium.factory import WebDriverFactory
from notion_zap.apps.media_scraper.helpers import remove_emoji
from notion_zap.apps.media_scraper.location.lib_struct import (
    LibraryScrapBase, LibraryScrapResult)
from notion_zap.apps.media_scraper.location.lib_gy import GoyangLibraryScrapBase
from notion_zap.apps.media_scraper.location.lib_snu import SNULibraryScrapBase
from notion_zap.apps.media_scraper.struct import ReadingPageEditor
from notion_zap.cli.utility import stopwatch


class LibraryScrapManager:
    base_classes: dict[str, type(LibraryScrapBase)] = {
        'gy': GoyangLibraryScrapBase,
        'snu': SNULibraryScrapBase,
    }

    def __init__(self, targets: set[str], create_window=False):
        self.targets = targets
        self.driver_factory = WebDriverFactory(create_window)
        self.bases: dict[str, LibraryScrapBase] = {
            key: base_cls(self.driver_factory)
            for key, base_cls in self.base_classes.items()
            if key in self.targets}

    def __call__(self, editor: ReadingPageEditor):
        results = self.scrap(*editor.titles)
        write_data(editor, results)

    def scrap(self, *titles: str) -> dict[str, LibraryScrapResult]:
        titles = set(remove_emoji(title) for title in titles)
        results = {}
        for key, base in self.bases.items():
            for title in titles:
                if res := base.scrap(title):
                    results[key] = res
                    stopwatch(f"{key}: {res}")
                    continue
        return results

    def quit(self):
        if any(base.driver_active for base in self.bases.values()):
            stopwatch('Selenium 마감..')
            for base in self.bases.values():
                base.quit_if_needed()
            stopwatch('Selenium 종료')


def write_data(editor: ReadingPageEditor, results: dict[str, LibraryScrapResult]):
    page = editor.page
    if results:
        location, available = parse_scrap_results(results)
        page.write_text(key_alias='location', value=location)
        page.write_checkbox(key_alias='not_available', value=not available)
    else:
        if not page.read_tag('location'):
            editor.mark_exception('no_location')


def parse_scrap_results(results: dict[str, LibraryScrapResult]):
    values = list(results.values())
    values.sort(reverse=True)
    available = values[0].available
    locations = ' '.join([str(value) for value in values if str(value)])
    return locations, available


if __name__ == '__main__':
    manager = LibraryScrapManager({'gy'}, create_window=True)
    print(manager.scrap('자기 인생의 철학자들').get('gy'))

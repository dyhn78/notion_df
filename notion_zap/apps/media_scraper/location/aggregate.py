from typing import Iterable

from notion_zap.apps.externals.selenium.factory import WebDriverFactory
from notion_zap.apps.media_scraper.helpers import remove_emoji
from notion_zap.apps.media_scraper.location.lib_gy import GoyangLibraryScrapBase
from notion_zap.apps.media_scraper.location.lib_snu import SNULibraryScrapBase
from notion_zap.apps.media_scraper.location.lib_struct import LibraryScrapBase
from notion_zap.cli.utility import stopwatch


class LibraryScraperAggregate:
    def __init__(self, targets: Iterable[str], create_window=False):
        self.targets = targets
        self.get_driver = WebDriverFactory(create_window)
        self.base_map_full: dict[str, LibraryScrapBase] = {
            'gy': GoyangLibraryScrapBase(self.get_driver),
            'snu': SNULibraryScrapBase(self.get_driver),
        }
        self.base_map: dict[str, LibraryScrapBase] = {
            key: base for key, base in self.base_map_full.items()
            if key in self.targets}

    def __call__(self, *titles: str):
        titles = set(remove_emoji(title) for title in titles)
        data = {}
        for key, base in self.base_map.items():
            for title in titles:
                if res := base.scrap(title):
                    data[key] = res
                    stopwatch(f"{key}: {res}")
        return data

    def quit_drivers(self):
        if any(base.driver_active for base in self.base_map.values()):
            stopwatch('Selenium 마감..')
            for base in self.base_map.values():
                base.quit_if_needed()
            stopwatch('Selenium 종료')


if __name__ == '__main__':
    agg = LibraryScraperAggregate({'gy'}, create_window=True)
    print(agg('가면의 생').get('gy'))

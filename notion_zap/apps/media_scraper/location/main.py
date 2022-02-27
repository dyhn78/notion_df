from typing import Optional

from notion_zap.apps.externals.selenium import SeleniumBaseDepr
from notion_zap.apps.media_scraper.struct import ReadingPageChecker
from notion_zap.apps.media_scraper.location import LibraryDataWriter
from notion_zap.apps.media_scraper.location.gy import GoyangLibraryAgent
from notion_zap.apps.media_scraper.location.snu import SNULibraryAgent
from notion_zap.apps.media_scraper.helpers import remove_emoji
from notion_zap.cli.utility import stopwatch


class LibraryManager:
    def __init__(self, global_tasks: set[str], create_window=False):
        self.global_tasks = global_tasks
        self.bases: list[SeleniumBaseDepr] = []
        if 'gy_lib' in self.global_tasks:
            self.base_gy = SeleniumBaseDepr(1, create_window)
            self.bases.append(self.base_gy)
        if 'snu_lib' in self.global_tasks:
            self.base_snu = SeleniumBaseDepr(1, create_window)
            self.bases.append(self.base_snu)

    def start(self):
        for base in self.bases:
            base.start()

    def quit(self):
        for base in self.bases:
            base.quit()

    def __del__(self):
        self.quit()

    def __call__(self, checker: ReadingPageChecker, tasks: set[str]):
        data = self.scrap(checker, tasks)
        LibraryDataWriter(checker, data)

    def scrap(self, checker: ReadingPageChecker, tasks: set[str]):
        data = {}
        book_names = checker.names
        if 'snu_lib' in tasks:
            if snu_lib := self.scrap_snu(*book_names):
                stopwatch(f'서울대: {snu_lib}')
                data.update(snu=snu_lib)
        if 'gy_lib' in tasks:
            if gy_lib := self.scrap_gy(*book_names):
                stopwatch(f"고양시: {gy_lib['lib_name']}  {gy_lib['book_code']}")
                data.update(gy=gy_lib)
        return data

    @staticmethod
    def scrap_by(agent_cl, base: SeleniumBaseDepr, *titles: str):
        for title in set(remove_emoji(text) for text in titles):
            agent = agent_cl(base, title)
            if lib_info := agent():
                return lib_info

    def scrap_snu(self, *book_names: str) -> Optional[str]:
        return self.scrap_by(SNULibraryAgent, self.base_snu, *book_names)

    def scrap_gy(self, *book_names: str) -> Optional[dict]:
        return self.scrap_by(GoyangLibraryAgent, self.base_gy, *book_names)


if __name__ == '__main__':
    manager = LibraryManager({'gy_lib'}, create_window=True)
    manager.start()
    gy = GoyangLibraryAgent('책 이름', manager.base_gy)

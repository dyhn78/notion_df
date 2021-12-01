from notion_zap.apps.externals.selenium import SeleniumBase
from notion_zap.apps.media_scraper.module_lib import LibraryDataWriter
from notion_zap.apps.media_scraper.module_lib.gy import GoyangLibraryAgent
from notion_zap.apps.media_scraper.module_lib.snu import SNULibraryAgent
from notion_zap.apps.media_scraper.structs.controller_base_logic import ReadingPageWriter
from notion_zap.cli.utility import stopwatch


class LibraryManager:
    GY = GoyangLibraryAgent
    SNU = SNULibraryAgent

    def __init__(self, tasks: set[str]):
        self.tasks = tasks
        self.bases: list[SeleniumBase] = []
        if 'gy_lib' in self.tasks:
            self.base_gy = SeleniumBase(2)
            self.bases.append(self.base_gy)
        if 'snu_lib' in self.tasks:
            self.base_snu = SeleniumBase(1)
            self.bases.append(self.base_snu)

    def start(self):
        for base in self.bases:
            base.start()

    def quit(self):
        for base in self.bases:
            base.quit()

    def __del__(self):
        self.quit()

    def execute(self, status: ReadingPageWriter, tasks: set):
        writer = LibraryDataWriter(status)
        data = self.scrap(status, tasks)
        try:
            first_lib = self.prioritize_data(data)
        except ValueError:
            print(f"page.title={status.page.title}, {data=}")
            return False
        else:
            writer.set_lib_data(data, first_lib)

    def scrap(self, status: ReadingPageWriter, tasks: set):
        data = {}
        book_names = status.book_names
        if 'snu_lib' in tasks:
            snu_lib = self.SNU(self.base_snu, book_names).execute()
            if snu_lib:
                stopwatch(f'서울대: {snu_lib}')
                data.update(snu=snu_lib)
        if 'gy_lib' in tasks:
            gy_lib = self.GY(self.base_gy, book_names).execute()
            if gy_lib:
                stopwatch(f"고양시: {gy_lib['lib_name']}  {gy_lib['book_code']}")
                data.update(gy=gy_lib)
        return data

    @staticmethod
    def prioritize_data(data: dict):
        if 'gy' in data.keys() and \
                data['gy']['lib_name'] == GoyangLibraryAgent.GAJWA_LIB:
            return 'gy'
        elif 'snu' in data.keys():
            return 'snu'
        elif 'gy' in data.keys():
            return 'gy'
        raise ValueError

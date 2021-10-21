from typing import Union

from notion_py.interface.utility import stopwatch
from .gy_selenium import GoyangLibrary
from .snu_selenium import SNULibrary
from ..regular_scrap import ReadingDBScrapController, ReadingPageScrapController


class LibraryScrapManager:
    def __init__(self, caller: ReadingDBScrapController):
        self.caller = caller
        self.tasks = caller.tasks
        self.gylib = GoyangLibrary() if 'gy_lib' in self.tasks else None
        self.snulib = SNULibrary() if 'snu_lib' in self.tasks else None

    def execute(self, page_cont: ReadingPageScrapController):
        scraper = LibraryScraper(self, page_cont)
        scraper.execute()


class LibraryScraper:
    def __init__(self, caller: LibraryScrapManager,
                 cont: ReadingPageScrapController):
        self.caller = caller
        self.cont = cont
        self.page = self.cont.page
        self.tasks = self.cont.tasks
        self.book_names = self.cont.get_names()

    def execute(self):
        data = self.scrap()
        try:
            first_lib = self.prioritize_data(data)
        except ValueError:
            self.cont.set_as_lib_missing()
        else:
            self.set_lib_data(data, first_lib)

    def scrap(self):
        data = {}
        if 'snu_lib' in self.tasks:
            # noinspection PyTypeChecker
            snu_lib = self.caller.snulib.execute(self.book_names)
            if snu_lib:
                stopwatch(f'서울대: {snu_lib}')
                data.update(snu=snu_lib)
        if 'gy_lib' in self.tasks:
            # noinspection PyTypeChecker
            gy_lib = self.caller.gylib.execute(self.book_names)
            if gy_lib:
                stopwatch(f"고양시: {gy_lib['lib_name']}  {gy_lib['book_code']}")
                data.update(gy=gy_lib)
        return data

    @staticmethod
    def prioritize_data(data: dict):
        if 'gy' in data.keys() and \
                data['gy']['lib_name'] == GoyangLibrary.GAJWA_LIB:
            return 'gy'
        elif 'snu' in data.keys():
            return 'snu'
        elif 'gy' in data.keys():
            return 'gy'
        raise ValueError

    def set_lib_data(self, data, first_lib):
        datastrings = []
        first_data = data.pop(first_lib)
        string, available = self._parse_mixed_datum(first_data)
        datastrings.append(string)
        datastrings.extend([self._parse_mixed_datum(data)[0]
                            for lib, data in data.items()])
        joined_string = '; '.join(datastrings)

        self.page.props.write_text_at('location', joined_string)
        self.page.props.write_checkbox_at('not_available', not available)

    @staticmethod
    def _parse_mixed_datum(res: Union[dict, str]) -> tuple[str, bool]:
        if type(res) == dict:
            string = f"{res['lib_name']}"
            if book_code := res['book_code']:
                string += f" {book_code}"
            available = res['available']
            return string, available
        elif type(res) == str:
            available = not ('불가능' not in res)
            return res, available

    # @staticmethod
    # def _parse_dict(res: dict):
    #     string = f"{res['lib_name']}"
    #     if book_code := res['book_code']:
    #         string += f" {book_code}"
    #     available = res['available']
    #     return string, available
    #
    # @staticmethod
    # def _parse_str(res: str):
    #     available = not ('불가능' not in res)
    #     return res, available

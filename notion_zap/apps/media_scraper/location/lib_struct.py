from abc import abstractmethod, ABC
from typing import Callable

from selenium.webdriver.chrome.webdriver import WebDriver


class LibraryScrapResult:
    def __init__(self, availability: bool, book_code=''):
        self.lib_name = ''
        self.book_code = book_code
        self.availability = availability

    def __str__(self):
        return "  ".join(val for val in [self.lib_name, self.book_code] if val)


class LibraryScrapBase(ABC):
    def __init__(self, driver_factory: Callable[[], WebDriver]):
        self.__get_driver = driver_factory
        self.__drivers: list[WebDriver] = []
        self.driver_active = False

    def get_drivers(self, num: int) -> list[WebDriver]:
        while len(self.__drivers) < num:
            driver = self.__get_driver()
            driver.start_client()
            self.__drivers.append(driver)
        return self.__drivers

    def get_driver(self):
        return self.get_drivers(1)[0]

    @abstractmethod
    def scrap(self, title: str) -> LibraryScrapResult:
        pass

    def quit_if_needed(self):
        if self.driver_active:
            for driver in self.__drivers:
                driver.quit()
        self.driver_active = False

    def __del__(self):
        self.quit_if_needed()

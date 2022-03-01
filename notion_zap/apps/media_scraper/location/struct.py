from abc import abstractmethod, ABC

from selenium.webdriver.chrome.webdriver import WebDriver


class LibraryScrapResult:
    def __init__(self, availability: bool, book_code=''):
        self.lib_name = ''
        self.book_code = book_code
        self.availability = availability

    def __str__(self):
        return "  ".join(val for val in [self.lib_name, self.book_code] if val)


class LibraryScrapBase(ABC):
    def __init__(self, *drivers: WebDriver):
        self.drivers = drivers
        self.driver_active = False

    @abstractmethod
    def scrap(self, title: str) -> LibraryScrapResult:
        pass

    def start_if_needed(self):
        if not self.driver_active:
            for driver in self.drivers:
                driver.start_client()
        self.driver_active = True

    def quit_if_needed(self):
        if self.driver_active:
            for driver in self.drivers:
                driver.quit()
        self.driver_active = False

    def __del__(self):
        self.quit_if_needed()

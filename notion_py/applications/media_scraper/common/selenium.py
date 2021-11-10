import os
from typing import Callable

from selenium import webdriver
from selenium.common.exceptions import \
    NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options

from notion_py.interface.common.utility import stopwatch


def retry_webdriver(function: Callable, recursion_limit=1) -> Callable:
    def wrapper(self, *args):
        for recursion in range(recursion_limit):
            if recursion != 0:
                stopwatch(f'selenium 재시작 {recursion}/{recursion_limit}회')
            try:
                response = function(self, *args)
                return response
            except (NoSuchElementException, StaleElementReferenceException):
                if recursion == recursion_limit:
                    return None

    return wrapper


class SeleniumScraper:
    DRIVER_CNT = 1

    def __init__(self):
        self.drivers = []
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        for i in range(self.DRIVER_CNT):
            driver = webdriver.Chrome(self.chromedriver_path, options=options,
                                      service_log_path=os.devnull)
            driver.minimize_window()
            self.drivers.append(driver)

    def start(self):
        for driver in self.drivers:
            driver.start_client()

    @property
    def chromedriver_path(self):
        # print(os.path.abspath('chromedriver.exe'))
        return os.path.join(os.getcwd(),
                            'notion_py', 'applications',
                            'chromedriver.exe')

    def quit(self):
        for driver in self.drivers:
            driver.quit()

    def __del__(self):
        self.quit()

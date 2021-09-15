import os
from typing import Callable
from selenium import webdriver
from selenium.common.exceptions import \
    NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options

from notion_py.interface.utility import stopwatch


def retry_webdriver(method: Callable, recursion_limit=3) -> Callable:
    def wrapper(self, *args, recursion=0):
        if recursion != 0:
            stopwatch(f'selenium 재시작 {recursion}/{recursion_limit}회')
        try:
            response = method(self, *args)
        except (NoSuchElementException, StaleElementReferenceException):
            if recursion == recursion_limit:
                return None
            # driver.stop_client()
            # driver.start_client()
            response = wrapper(self, recursion=recursion + 1)
        return response
    return wrapper


class SeleniumScraper:
    driver_num = 1

    def __init__(self):
        self.drivers = []
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        for i in range(self.driver_num):
            driver = webdriver.Chrome(self.chromedriver_path, options=options,
                                      service_log_path=os.devnull)
            driver.minimize_window()
            driver.start_client()
            self.drivers.append(driver)

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

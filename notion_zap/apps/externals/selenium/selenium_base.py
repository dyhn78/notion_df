import os
# import logging
from typing import Callable
from subprocess import CREATE_NO_WINDOW

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from notion_zap.cli.utility import stopwatch

# logging.basicConfig(filename='debug.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s %(name)s %(message)s')
# logger = logging.getLogger(__name__)


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


class SeleniumBase:
    CHROMEDRIVER_PATH = os.path.join(os.path.dirname(__file__), 'chromedriver95.exe')

    def __init__(self, driver_cnt: int):
        self.drivers = []
        self.driver_cnt = driver_cnt

    def start(self):
        # https://www.zacoding.com/en/post/python-selenium-hide-console/
        for i in range(self.driver_cnt):
            service = Service(
                self.CHROMEDRIVER_PATH,
                # log_path=os.path.join(os.path.dirname(__file__), 'selenium_log')
            )
            service.creationflags = CREATE_NO_WINDOW
            driver = webdriver.Chrome(service=service,
                                      options=self.options)
            self.drivers.append(driver)
            driver.start_client()

    def quit(self):
        for driver in self.drivers:
            driver.quit()

    @property
    def options(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        return options

    def __del__(self):
        self.quit()

import os
from typing import Callable
from subprocess import CREATE_NO_WINDOW

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from notion_zap.cli.utility import stopwatch


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
    DRIVER_CNT = 1
    CHROMEDRIVER_PATH = os.path.join(os.path.dirname(__file__), 'chromedriver95.exe')

    def __init__(self):
        self.drivers = []

    def start(self):
        # https://www.zacoding.com/en/post/python-selenium-hide-console/
        for i in range(self.DRIVER_CNT):
            service = Service(self.CHROMEDRIVER_PATH)
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

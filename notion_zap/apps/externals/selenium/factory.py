import os
from typing import Callable, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from notion_zap.cli.utility import stopwatch


class WebDriverFactory:
    ON_WINDOWS = os.name == 'nt'
    ON_LINUX = os.name == 'posix'

    def __init__(self, create_window=False):
        self.drivers: list[webdriver.Chrome] = []
        self.create_window = create_window

    def __call__(self, create_window: Optional[bool] = None):
        if create_window is None:
            create_window = self.create_window
        if create_window:
            driver = webdriver.Chrome(self.get_driver_path())
        else:
            driver = webdriver.Chrome(service=self.get_service_without_window(),
                                      options=self.get_options())
        self.drivers.append(driver)
        # driver.start_client()
        return driver

    @classmethod
    def get_driver_path(cls):
        if cls.ON_WINDOWS:
            return os.path.join(os.path.dirname(__file__), 'chromedriver.exe')
        elif cls.ON_LINUX:
            return os.path.join(os.path.dirname(__file__), 'chromedriver_linux')


    def get_service_without_window(self):
        # https://www.zacoding.com/en/post/python-selenium-hide-console/
        service = Service(
            self.get_driver_path(),
        )
        if self.ON_WINDOWS:
            from subprocess import CREATE_NO_WINDOW
            service.creationflags = CREATE_NO_WINDOW
        return service

    @staticmethod
    def get_options():
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        return options


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

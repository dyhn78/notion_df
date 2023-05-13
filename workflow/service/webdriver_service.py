import os
from typing import Callable

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class WebDriverFactory:
    ON_WINDOWS = (os.name == 'nt')

    def __init__(self, create_window: bool = False):
        self.drivers: list[webdriver.Chrome] = []
        self.create_window = create_window

    def __call__(self) -> webdriver.Chrome:
        service = Service(ChromeDriverManager().install())
        if not self.create_window and self.ON_WINDOWS:
            # https://www.zacoding.com/en/post/python-selenium-hide-console/
            from subprocess import CREATE_NO_WINDOW
            service.creationflags = CREATE_NO_WINDOW
        options = Options()
        if not self.create_window:
            options.add_argument('--headless')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(service=service, options=self.get_options())
        self.drivers.append(driver)
        return driver

    def __del__(self):
        for driver in self.drivers:
            driver.quit()

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
                print(f'selenium 재접속 {recursion}/{recursion_limit}회')
            try:
                response = function(self, *args)
                return response
            except (NoSuchElementException, StaleElementReferenceException):
                if recursion == recursion_limit:
                    return None

    return wrapper

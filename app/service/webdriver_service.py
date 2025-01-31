import os
from typing import Callable

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class WebDriverService:
    ON_WINDOWS = os.name == "nt"

    def __init__(self, create_window: bool):
        self.drivers: list[webdriver.Chrome] = []
        self.create_window = create_window

    def create(self) -> webdriver.Chrome:
        """
        with WebDriverService(...).create() as driver:
            # do your thing
        # driver.__exit__() will call quit()
        """
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        if not self.create_window and self.ON_WINDOWS:
            # https://www.zacoding.com/en/post/python-selenium-hide-console/
            from subprocess import CREATE_NO_WINDOW

            service.creationflags = CREATE_NO_WINDOW
        options = Options()
        options.add_argument("--incognito")
        if not self.create_window:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-setuid-sandbox")
        driver = webdriver.Chrome(
            executable_path=driver_path, service=service, options=options
        )
        self.drivers.append(driver)
        return driver


def retry_webdriver(function: Callable, recursion_limit=1) -> Callable:
    def wrapper(self, *args):
        for recursion in range(recursion_limit):
            if recursion != 0:
                print(f"selenium 재접속 {recursion}/{recursion_limit}회")
            try:
                response = function(self, *args)
                return response
            except (NoSuchElementException, StaleElementReferenceException):
                if recursion == recursion_limit:
                    return None

    return wrapper

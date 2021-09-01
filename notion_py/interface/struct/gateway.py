import os
import time
from abc import ABCMeta
from json import JSONDecodeError
from typing import Union, Callable

from notion_client import Client, AsyncClient
from notion_client.errors import APIResponseError

from notion_py.interface.utility import stopwatch
from .value_carrier import Requestor


def drop_empty_request(method: Callable):
    def wrapper(self, **kwargs):
        if not bool(self):
            return {}
        return method(self, **kwargs)
    return wrapper


def retry_request(func: Callable, recursion_limit=3):
    def wrapper(self, **kwargs):
        for recursion in range(recursion_limit - 1):
            try:
                return func(self, **kwargs)
            except (JSONDecodeError, APIResponseError):
                time.sleep(0.5 * (2 ** recursion))
            if recursion:
                stopwatch(f'Notion 응답 재시도 {recursion + 1}/{recursion_limit}회')
        func(self, **kwargs)
    return wrapper


class Gateway(Requestor, metaclass=ABCMeta):
    _token = os.environ['NOTION_TOKEN'].strip("'").strip('"')
    notion: Union[Client, AsyncClient] = Client(auth=_token)

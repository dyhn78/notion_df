import os
import time
from abc import abstractmethod
from json import JSONDecodeError
from typing import Union, Callable

from notion_client import Client, AsyncClient
from notion_client.errors import APIResponseError

from .carriers import Requestor
from notion_py.utility import stopwatch


def retry_request(method: Callable, recursion_limit=5):
    def wrapper(self, **kwargs):
        for recursion in range(recursion_limit - 1):
            try:
                return method(self, **kwargs)
            except (JSONDecodeError, APIResponseError):
                time.sleep(0.5 * (2 ** recursion))
            if recursion:
                stopwatch(f'Notion 응답 재시도 {recursion + 1}/{recursion_limit}회')
        method(self, **kwargs)
    return wrapper


class GatewayRequestor(Requestor):
    _token = os.environ['NOTION_TOKEN'].strip("'").strip('"')
    notion: Union[Client, AsyncClient] = Client(auth=_token)

    @abstractmethod
    def __bool__(self):
        pass

    @retry_request
    @abstractmethod
    def execute(self) -> dict:
        if not bool(self):
            return {}
        pass
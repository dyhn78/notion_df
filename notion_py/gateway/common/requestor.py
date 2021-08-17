import os
import time
from abc import abstractmethod
from collections import defaultdict
from json import JSONDecodeError
from typing import Union, Callable

from notion_client import Client, AsyncClient
from notion_client.errors import APIResponseError

from notion_py.gateway.common import Structure
from notion_py.utility import page_id_to_url, stopwatch


def retry_request(method: Callable, recursion_limit=5):
    def wrapper(self, **kwargs):
        for recursion in range(recursion_limit - 1):
            if recursion:
                stopwatch(f'Notion 응답 재시도 {recursion}/{recursion_limit}회')
            try:
                return method(self, **kwargs)
            except (JSONDecodeError, APIResponseError):
                time.sleep(0.5 * (2 ** recursion))
        method(self, **kwargs)
    return wrapper


class Requestor(Structure):
    page_id = ''

    @property
    def notion(self) -> Union[Client, AsyncClient]:
        token = os.environ['NOTION_TOKEN'].strip("'").strip('"')
        return Client(auth=token)

    @abstractmethod
    def apply(self):
        pass

    @retry_request
    @abstractmethod
    def execute(self):
        pass

    def print_url(self, string, page_id=''):
        page_id = self.page_id if not page_id else page_id
        if page_id:
            stopwatch(' '.join([string, page_id_to_url(page_id)]))

    @classmethod
    def _zip_dict(cls, *dicts: Union[dict, None]):
        res = defaultdict(list)
        for carrier in dicts:
            if carrier is None:
                continue
            for key, value in carrier.items():
                res[key].append(value)
        return res



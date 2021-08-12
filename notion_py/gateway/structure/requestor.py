import os
from abc import abstractmethod
import time
from typing import Union, Callable
from collections import defaultdict
from json import JSONDecodeError

from notion_client import Client, AsyncClient
from notion_client.errors import APIResponseError

from notion_py.gateway.structure import Structure
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
    parent_id = ''

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
        page_id = self.parent_id if not page_id else page_id
        if page_id:
            stopwatch(' '.join([string, page_id_to_url(page_id)]))

    @classmethod
    def _merge_dict(cls, *dicts: Union[dict, None]):
        res = {}
        for carrier in dicts:
            if carrier is None:
                continue
            for key, value in carrier.items():
                res[key] = value
        return res

    @classmethod
    def _zip_dict(cls, *dicts: Union[dict, None]):
        res = defaultdict(list)
        for carrier in dicts:
            if carrier is None:
                continue
            for key, value in carrier.items():
                res[key].append(value)
        return res


class LongRequestor(Requestor):
    MAX_PAGE_SIZE = 100
    INF = int(1e5) - 1

    @abstractmethod
    @retry_request
    def _execute_once(self, page_size=None, start_cursor=None):
        pass

    def execute(self, page_size=INF):
        res = []
        result = {'results': res}
        if page_size == 0:
            page_size = self.INF
        has_more = True
        start_cursor = None
        page_retrieved = 0
        while has_more and page_size > 0:
            # noinspection PyArgumentList
            response = self._execute_once(page_size=min(page_size, self.MAX_PAGE_SIZE),
                                          start_cursor=start_cursor)
            has_more = response['has_more']
            start_cursor = response['next_cursor']
            res.extend(response['results'])

            page_size -= self.MAX_PAGE_SIZE
            page_retrieved += len(response['results'])
            stopwatch(f'{page_retrieved} 개 완료')
        return result

import os
from abc import abstractmethod
from json import JSONDecodeError
from typing import Union, Callable
from collections import defaultdict

from notion_client import Client, AsyncClient

from notion_py.interface.structure import Structure
from notion_py.helpers import page_id_to_url, stopwatch


def retry(method: Callable, recursion_limit=5):
    def wrapper(self, recursion=recursion_limit, **kwargs):
        try:
            response = method(self, **kwargs)
        except JSONDecodeError:
            if recursion == 0:
                raise RecursionError
            response = wrapper(recursion - 1)
        return response

    return wrapper


def ignore_if_empty(method: Callable):
    def wrapper(self, **kwargs):
        if not self:
            return {}
        else:
            return method(self, **kwargs)
    return wrapper


class Requestor(Structure):
    _id_raw = ''

    @property
    def notion(self) -> Union[Client, AsyncClient]:
        # TODO: .env 파일에 토큰 숨기기
        os.environ['NOTION_TOKEN'] = ***REMOVED***
        return Client(auth=os.environ['NOTION_TOKEN'])

    @abstractmethod
    def apply(self):
        pass

    @retry
    @abstractmethod
    def execute(self):
        pass

    def print_info(self, *string):
        if self._id_raw:
            print(*string, page_id_to_url(self._id_raw), sep='; ')

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


class RecursiveRequestor(Requestor):
    MAX_PAGE_SIZE = 100
    INF = int(1e9)

    @retry
    @abstractmethod
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
            response = self._execute_once(self, page_size=min(page_size, self.MAX_PAGE_SIZE),
                                          start_cursor=start_cursor)
            has_more = response['has_more']
            start_cursor = response['next_cursor']
            res.extend(response['results'])

            page_size -= self.MAX_PAGE_SIZE
            page_retrieved += len(response['results'])
            stopwatch(f'{page_retrieved} 개 완료')
        return result

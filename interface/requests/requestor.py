import os
from abc import abstractmethod
from typing import Union
from collections import defaultdict

from notion_client import Client, AsyncClient

from interface.requests.structures import Structure
from stopwatch import stopwatch


class Requestor(Structure):
    notion: Union[Client, AsyncClient]

    @property
    def notion(self):
        # TODO: .env 파일에 토큰 숨기기
        os.environ['NOTION_TOKEN'] = ***REMOVED***
        return Client(auth=os.environ['NOTION_TOKEN'])

    @abstractmethod
    def execute(self):
        pass

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

    @abstractmethod
    def _execute_once(self, page_size=None, start_cursor=None):
        pass

    def execute(self, page_size=INF):
        res = []
        has_more = True
        start_cursor = None
        page_retrieved = 0
        while has_more and page_size > 0:
            response = self._execute_once(page_size=min(page_size, self.MAX_PAGE_SIZE),
                                          start_cursor=start_cursor)
            has_more = response['has_more']
            start_cursor = response['next_cursor']
            res.extend(response['results'])

            page_size -= self.MAX_PAGE_SIZE
            page_retrieved += len(response['results'])
            stopwatch(f'{page_retrieved} 개 완료')
        return {'results': res}

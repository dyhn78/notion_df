import os
import time
from abc import ABCMeta, abstractmethod
from json import JSONDecodeError
from typing import Union, Callable

from notion_client import Client, AsyncClient
from notion_client.errors import APIResponseError

from notion_py.interface.utility import stopwatch
from .carrier import Requestor, ValueCarrier


class Gateway(Requestor, ValueCarrier, metaclass=ABCMeta):
    _token = os.environ['NOTION_TOKEN'].strip("'").strip('"')
    notion: Union[Client, AsyncClient] = Client(auth=_token)

    def __init__(self, target_id: str):
        self.target_id = target_id


def drop_empty_request(method: Callable):
    def wrapper(self, **kwargs):
        if not bool(self):
            return {}
        return method(self, **kwargs)
    return wrapper


def retry_request(func: Callable, recursion_limit=3):
    def wrapper(self, **kwargs):
        recursion = 0
        while True:
            try:
                response = func(self, **kwargs)
                return response
            except (JSONDecodeError, APIResponseError) as e:
                if recursion == recursion_limit:
                    raise e
                recursion += 1
                stopwatch(f'Notion 응답 재시도 {recursion}/{recursion_limit}회')
                time.sleep(1 * (1 ** recursion))
    return wrapper


class LongGateway(Gateway):
    MAX_PAGE_SIZE = 100
    INF = int(1e5) - 1

    def __init__(self, target_id: str, target_name=''):
        super().__init__(target_id)
        self.target_name = target_name

    @abstractmethod
    @retry_request
    def _execute_once(self, page_size=None, start_cursor=None):
        pass

    def execute(self, page_size=0):
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

            comments = f'{page_retrieved} 개 완료'
            if self.target_name:
                comments += f' << {self.target_name}'
            stopwatch(comments)
        return result

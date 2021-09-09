import time
from abc import ABCMeta, abstractmethod
from json import JSONDecodeError
from pprint import pprint
from typing import Callable, Optional

from notion_client.errors import APIResponseError

from notion_py.interface.utility import stopwatch
from .carrier import Requestor, ValueCarrier
from .editor import Editor


class GroundEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self.gateway: Optional[Gateway] = None
        self.enable_overwrite = True

    def __bool__(self):
        return bool(self.gateway)

    def set_overwrite_option(self, option: bool):
        self.enable_overwrite = option

    def preview(self):
        return self.gateway.unpack() if self.gateway else {}

    def execute(self):
        return self.gateway.execute() if self.gateway else {}


class Gateway(Requestor, ValueCarrier, metaclass=ABCMeta):
    def __init__(self, editor: Editor):
        self.editor = editor
        self.notion = editor.root_editor.notion

    @property
    def target_id(self):
        return self.editor.master_id

    @property
    def target_name(self):
        return self.editor.master.master_name


def drop_empty_request(method: Callable):
    def wrapper(self, **kwargs):
        if not bool(self):
            return {}
        return method(self, **kwargs)
    return wrapper


def retry_request(func: Callable, recursion_limit=1):
    def wrapper(self: Gateway, **kwargs):
        recursion = 0
        while True:
            try:
                response = func(self, **kwargs)
                return response
            except (JSONDecodeError, APIResponseError) as e:
                if recursion == recursion_limit:
                    pprint(self.unpack())
                    raise e
                recursion += 1
                stopwatch(f'Notion 응답 재시도 {recursion}/{recursion_limit}회')
                time.sleep(1 * (1 ** recursion))
    return wrapper


class LongGateway(Gateway):
    MAX_PAGE_SIZE = 100
    INF = int(1e5) - 1

    def __init__(self, editor: Editor):
        super().__init__(editor)

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

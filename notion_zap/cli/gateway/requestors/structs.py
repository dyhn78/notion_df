import time
from abc import ABCMeta, abstractmethod
from typing import Callable

from notion_client.errors import APIResponseError

from notion_zap.cli.utility import stopwatch
from notion_zap.cli.editors.structs.leaders import Component
from notion_zap.cli.structs.base_logic import Executable, ValueCarrier


class Requestor(Executable, ValueCarrier, metaclass=ABCMeta):
    pass


class PointRequestor(Requestor, metaclass=ABCMeta):
    def __init__(self, editor: Component):
        self.editor = editor
        self.client = editor.root.client

    def __str__(self):
        return f"{type(self).__name__}"

    @property
    def target_id(self):
        return self.editor.block_id

    @property
    def target_name(self):
        return self.editor.block_name

    @property
    def target_url(self):
        return self.editor.block_url


class LongRequestor(PointRequestor):
    MAX_PAGE_SIZE = 100
    INF = int(1e5) - 1

    def __init__(self, editor: Component):
        super().__init__(editor)
        self.response_size = 0
        self.has_more = True
        self.start_cursor = None

    @abstractmethod
    def execute(self, request_size=0):
        self._execute_all(request_size, False)

    def _execute_all(self, request_size, print_comments_each: bool):
        res = []
        result = {'results': res}
        if request_size == 0:
            request_size = self.INF

        while self.has_more and (request_size > self.response_size):
            req_size = min(request_size - self.response_size,
                           self.MAX_PAGE_SIZE)
            # noinspection PyArgumentList
            response = self._execute_each(
                request_size=req_size,
                start_cursor=self.start_cursor)
            res.extend(response['results'])
            resp_size = len(response['results'])
            self.response_size += resp_size
            self.has_more = response['has_more']
            self.start_cursor = response['next_cursor']
            if print_comments_each:
                self._print_comments_each()
        return result

    @abstractmethod
    def _execute_each(self, request_size, start_cursor=None):
        pass

    def _print_comments_each(self):
        comments = f'→ {self.response_size} 개 완료'
        stopwatch(comments)


def drop_empty_request(method: Callable):
    def wrapper(self: Requestor, **kwargs):
        if self.__bool__():
            return method(self, **kwargs)
        else:
            if isinstance(self, LongRequestor):
                placeholder = []
            else:
                placeholder = {}
            return {'results': placeholder,
                    'context': f'dropped_empty_request_at_{self}'}

    return wrapper


# JSONDecodeError 처리 로직 추가
def print_response_error(func: Callable):
    def wrapper(self: PointRequestor, **kwargs):
        try:
            response = func(self, **kwargs)
            return response
        except APIResponseError as api_response_error:
            print()
            print(f'Error occurred while executing {str(self)} ::')
            self.preview()
            print()
            raise api_response_error

    return wrapper


def retry_then_print_response_error(func: Callable, recursion_limit=1, time_to_sleep=1):
    def wrapper(self: PointRequestor, **kwargs):
        recursion = 0
        while True:
            try:
                response = func(self, **kwargs)
                return response
            except APIResponseError as api_response_error:
                if recursion == recursion_limit:
                    print()
                    print(f'Error occurred while executing {str(self)} ::')
                    self.preview()
                    print()
                    raise api_response_error
                recursion += 1
                stopwatch(f'응답 재시도 {recursion}/{recursion_limit}회')
                time.sleep(time_to_sleep * (1 ** recursion))

    return wrapper

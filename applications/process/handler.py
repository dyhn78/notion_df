from __future__ import annotations
from abc import abstractmethod
from typing import Union

from interface.parse.databases import PageListParser
from interface.parse.pages import PagePropertyParser
from interface.requests.requestor import Requestor


class Handler:
    _requests_queue = []
    _reprocess_queue = []
    process_count = 0

    @abstractmethod
    def execute(self, reprocess_outside=False, async_client=False) -> Union[None, list]:
        pass

    def _send_request(self):
        for request in self._requests_queue:
            request.execute()
        self._requests_queue.clear()

    def _send_request_async(self):
        # TODO : 비동기 프로그래밍 구현
        self._requests_queue.clear()

    def _append_requests(self, task: Requestor):
        self._requests_queue.append(task)
        self.process_count += 1

    def _append_reprocess(self, task: PagePropertyParser):
        self._reprocess_queue.append(task)
        self.process_count += 1

    def extend_reprocess_queue(self, queue: list[PagePropertyParser]):
        self._reprocess_queue.extend(queue)


class PropertyHandler(Handler):
    def __init__(self, domain: PageListParser):
        self._domain = domain

    @abstractmethod
    def process_unit(self, dom: PagePropertyParser):
        """
        프로세싱이 성공했거나 필요없었던 대상이라면 False 를,
        리프로세싱이 필요하면 True 혹은 관련 인자(bool 값이 True 여야 함)를 반환한다.
        """
        pass

    def _execute_these(self, doms: list[PagePropertyParser]):
        for dom in doms.copy():
            self.process_unit(dom)

    def execute(self, reprocess_outside=False, async_client=False) -> PageListParser:
        self._execute_these(self._domain.list_of_objects)

        if not async_client:
            self._send_request()
        else:
            self._send_request_async()
        queue = self._reprocess_queue

        if not reprocess_outside:
            self._execute_these(self._reprocess_queue)
            self._reprocess_queue.clear()

            if not async_client:
                self._send_request()
            else:
                self._send_request_async()

        return PageListParser(queue)


class DomParser:
    def __init__(self, caller: type(PropertyHandler), dom: PagePropertyParser):
        self.caller = caller
        self.dom = dom

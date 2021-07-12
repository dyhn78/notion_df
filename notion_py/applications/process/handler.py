from __future__ import annotations
from abc import abstractmethod
from typing import Union

from notion_py.interface.parse import PageProperty, PagePropertyList
from notion_py.interface.structure import Requestor


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

    def _append_reprocess(self, task: PageProperty):
        self._reprocess_queue.append(task)
        self.process_count += 1

    def extend_reprocess_queue(self, queue: list[PageProperty]):
        self._reprocess_queue.extend(queue)


class PropertyHandler(Handler):
    def __init__(self, domain: PagePropertyList):
        self._domain = domain

    @abstractmethod
    def process_unit(self, dom: PageProperty):
        """
        프로세싱이 성공했거나 필요없었던 대상이라면 False 를,
        리프로세싱이 필요하면 True 혹은 관련 인자(bool 값이 True 여야 함)를 반환한다.
        """
        pass

    def _execute_these(self, doms: list[PageProperty]):
        for dom in doms.copy():
            self.process_unit(dom)

    def execute(self, reprocess_outside=False, async_client=False) -> PagePropertyList:
        self._execute_these(self._domain.parsed_pages)

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

        return PagePropertyList(self._domain.database_id, queue)


class DomParser:
    def __init__(self, caller: type(PropertyHandler), dom: PageProperty):
        self.caller = caller
        self.dom = dom

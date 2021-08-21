from __future__ import annotations
from abc import abstractmethod
from typing import Union

from notion_py.gateway.parse import PageParser, PageListParser
from notion_py.gateway.common import GatewayRequestor


class RequestStack:
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

    def _append_requests(self, task: GatewayRequestor):
        self._requests_queue.append(task)
        self.process_count += 1

    def _append_reprocess(self, task: PageParser):
        self._reprocess_queue.append(task)
        self.process_count += 1


class PropertyRequestStack(RequestStack):
    def __init__(self, domain: PageListParser):
        self._domain = domain

    @abstractmethod
    def process_unit(self, dom: PageParser):
        """
        프로세싱이 성공했거나 필요없었던 대상이라면 False 를,
        리프로세싱이 필요하면 True 혹은 관련 인자(bool 값이 True 여야 함)를 반환한다.
        """
        pass

    def _execute_these(self, doms: list[PageParser]):
        for dom in doms.copy():
            try:
                self.process_unit(dom)
            except:  # 삭제 예정
                from notion_py.utility import page_id_to_url
                print(f'error at: {dom.title}:: {page_id_to_url(dom.page_id)}')

    def execute(self, reprocess_outside=False, async_client=False) -> PageListParser:
        self._execute_these(self._domain.values)

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

        return PageListParser(queue, self._domain.parent_id)


class DomParser:
    def __init__(self, caller: type(PropertyRequestStack), dom: PageParser):
        self.caller = caller
        self.dom = dom

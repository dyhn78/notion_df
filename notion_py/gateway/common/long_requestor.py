from abc import abstractmethod

from notion_py.gateway.common import Requestor, retry_request
from notion_py.utility import stopwatch


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
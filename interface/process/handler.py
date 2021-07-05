from abc import abstractmethod

from interface.parse.databases import PageListParser
from interface.parse.pages import PagePropertyParser
from interface.requests.requestor import Requestor
from stopwatch import stopwatch


class Handler:
    requests_queue = []
    reprocess_queue = []
    process_count = 0

    def _append_requests(self, task: Requestor):
        self.requests_queue.append(task)
        # print(Handler.requests_queue)
        self.process_count += 1
        if (Handler.process_count - 10) == 0:
            stopwatch('10개')

    def _append_reprocess(self, task: PagePropertyParser):
        self.reprocess_queue.append(task)
        print(self.requests_queue)
        self.process_count += 1

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def execute_async(self):
        pass

    def _reexecute(self):
        self.__execute_once()
        self._reprocess()
        self.__execute_once()

    def _reexecute_async(self):
        self.__execute_once_async()
        self._reprocess_async()
        self.__execute_once_async()

    def __execute_once(self):
        for request in self.requests_queue:
            request.execute()
        self.requests_queue.clear()

    def __execute_once_async(self):
        # TODO : 비동기 프로그래밍 구현
        self.requests_queue.clear()
        pass

    @abstractmethod
    def _reprocess(self):
        self.reprocess_queue.clear()

    @abstractmethod
    def _reprocess_async(self):
        self.reprocess_queue.clear()
        pass


class PropertyHandler(Handler):
    requests_queue = []
    reprocess_queue = []

    def __init__(self, domain: PageListParser):
        self._domain = domain

    @abstractmethod
    def _process_unit(self, dom: PagePropertyParser):
        pass

    def execute(self):
        for dom in self._domain.list_of_objects:
            self._process_unit(dom)
        super()._reexecute()

    def execute_async(self):
        for dom in self._domain.list_of_objects:
            self._process_unit(dom)
        super()._reexecute_async()

    def _reprocess(self):
        for dom in self.reprocess_queue:
            self._process_unit(dom)
        super()._reprocess()

    def _reprocess_async(self):
        pass
        super()._reprocess_async()

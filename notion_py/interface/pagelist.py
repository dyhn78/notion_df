from typing import Optional

from ..gateway.structure import Requestor
from ..gateway.parse import PageListParser
from .dataframe import DataFrame


class PageList(Requestor):
    def __init__(self, query_response: dict, frame: Optional[DataFrame] = None):
        if frame is None:
            frame = DataFrame.create_dummy()
        self.frame = frame
        self.request_update = None

    def _parse_result(self, query_response):
        page_list_parser = PageListParser.from_query_response(query_response)
        for key in self.frame.props:
            pass
        return

    def apply(self):
        pass

    def execute(self):
        pass

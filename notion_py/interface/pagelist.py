from typing import Optional

import dataframe
from ..gateway.common import Requestor
from ..gateway.parse import PageListParser


class PageList(Requestor):
    def __init__(self, query_response: dict,
                 frame: Optional[dataframe.DataFrame] = None):
        if frame is None:
            frame = dataframe.DataFrame.create_dummy()
        self.frame = frame

        parsed_query = PageListParser.from_query_response(query_response)
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

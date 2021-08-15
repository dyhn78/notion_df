from typing import Optional

from .frame_property import PropertyFrame
from ..gateway.common import Requestor
from ..gateway.parse import PageListParser


class PageList(Requestor):
    def __init__(self, query_response: dict,
                 frame: Optional[PropertyFrame] = None):
        if frame is None:
            frame = PropertyFrame()
        self.frame = frame

        parsed_query = PageListParser.from_query_response(query_response)
        self.values = None

    def _parse_result(self, query_response):
        page_list_parser = PageListParser.from_query_response(query_response)
        for key in self.frame:
            pass
        return

    def apply(self):
        pass

    def execute(self):
        pass

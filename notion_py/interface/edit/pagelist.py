from typing import Optional

from notion_py.interface.preset.property import PropertyFrame
from notion_py.gateway.common import GatewayRequestor
from notion_py.gateway.parse import PageListParser


class PageList(GatewayRequestor):
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

    def unpack(self):
        pass

    def execute(self):
        pass

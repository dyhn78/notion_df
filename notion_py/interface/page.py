from typing import Optional

from ..gateway.common import Requestor
from ..gateway.parse import PageParser
from ..gateway.write import UpdateTabularPage, UpdateBasicPage
from .dataframe import DataFrame


class BasicPage(Requestor):
    def __init__(self, retrieve_response: dict,
                 page_id: Optional[str]):
        page_parser = PageParser.from_retrieve_response(retrieve_response)
        if page_id:
            self.request_update = UpdateBasicPage(page_id)

    def apply(self):
        pass

    def execute(self):
        pass

    def read_title(self):
        pass

    def read_rich_title(self):
        pass

    def write_title(self):
        pass

    def write_rich_title(self):
        pass


class TabularPage(Requestor):
    def __init__(self, page_id: Optional[str], frame: Optional[DataFrame] = None):
        if frame is None:
            frame = DataFrame.create_dummy()
        self.frame = frame
        if page_id:
            self.request_update = UpdateTabularPage(page_id)

    @classmethod
    def from_retrieve(cls, retrieve_response: dict,
                      page_id: Optional[str] = None, frame: Optional[DataFrame] = None):
        page_parser = PageParser.from_retrieve_response(retrieve_response)
        return cls(page_id, frame)

    def apply(self):
        pass

    def execute(self):
        pass

    def read(self, prop_name: str):
        pass

    def read_rich(self, prop_name: str):
        pass

    def read_on(self, prop_key: str):
        pass

    def read_rich_on(self, prop_key: str):
        pass

    def read_all(self):
        pass

    def read_all_keys(self):
        pass

    def write(self, prop_name: str):
        pass

    def write_rich(self, prop_name: str):
        pass

    def write_on(self, prop_key: str):
        pass

    def write_rich_on(self, prop_key: str):
        pass

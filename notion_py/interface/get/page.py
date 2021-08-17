from typing import Optional, Any

from .property import PropertyFrame
from .database import DatabaseGetter
from ..page import TabularPage
from ..parse import PageParser
from notion_py.gateway.others import RetrievePage


class TabularPageGetter:
    def __init__(self, page_id: str,
                 database_name: Optional[str] = None,
                 properties: Optional[dict[str, Any]] = None,
                 page_editor=TabularPage):
        self.page_id = page_id
        self.database_name = database_name
        self.frame = PropertyFrame(properties)
        self.unit = page_editor

    @classmethod
    def import_database_frame(cls, page_id: str, frame: DatabaseGetter):
        return cls(page_id, frame.database_name, frame.frame, frame.unit)

    @classmethod
    def create_dummy(cls):
        return cls('', '')

    def retrieve(self):
        retrieve = RetrievePage(self.page_id)
        response = retrieve.execute()
        page_parser = PageParser.fetch_retrieve(response)

        return TabularPage(
            page_id=self.page_id,
            title=page_parser.title,
            frame=self.frame,
            prop_plain=page_parser.props,
            prop_rich=page_parser.props_rich
        )

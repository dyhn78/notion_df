from typing import Optional, Any

from .property import PropertyFrame
from .database import DatabasePreset
from ..edit.tabular_page import TabularPage


class TabularPagePreset:
    def __init__(self, page_id: str,
                 database_name: Optional[str] = None,
                 properties: Optional[dict[str, Any]] = None,
                 page_editor=TabularPage):
        self.page_id = page_id
        self.database_name = database_name
        self.frame = PropertyFrame(properties)
        self.unit = page_editor

    @classmethod
    def import_database_frame(cls, page_id: str, frame: DatabasePreset):
        return cls(page_id, frame.database_name, frame.frame, frame.unit)

    @classmethod
    def create_dummy(cls):
        return cls('', '')

    def open_editor(self):
        return TabularPage(self.page_id)

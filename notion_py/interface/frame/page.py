from typing import Optional, Any

from .property_deprecated import PropertyFrameDeprecated
from .database_deprecated import DatabaseFrameDeprecated
from notion_py.interface.edit.tabular_page import TabularPage


class TabularPagePreset:
    def __init__(self, page_id: str,
                 database_name: Optional[str] = None,
                 properties: Optional[dict[str, Any]] = None,
                 page_editor=TabularPage):
        self.page_id = page_id
        self.database_name = database_name
        self.frame = PropertyFrameDeprecated(properties)
        self.unit = page_editor

    @classmethod
    def import_database_frame(cls, page_id: str, frame: DatabaseFrameDeprecated):
        return cls(page_id, frame.database_name, frame.frame, frame.unit)

    @classmethod
    def create_dummy(cls):
        return cls('', '')

    def open_editor(self):
        return TabularPage(self.page_id)

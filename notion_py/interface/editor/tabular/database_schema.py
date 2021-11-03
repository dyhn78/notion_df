from typing import Union

from notion_py.interface.common.struct import Requestor
from notion_py.interface.editor.common.struct import BlockEditor
from notion_py.interface.editor.common.struct.agents import GroundEditor


class DatabaseSchema(GroundEditor):
    @property
    def requestor(self) -> Union[Requestor, BlockEditor]:
        return None

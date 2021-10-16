from typing import Union

from notion_py.interface.common.struct import Requestor
from notion_py.interface.editor.struct import GroundEditor, PointEditor


class DatabaseSchema(GroundEditor):
    @property
    def gateway(self) -> Union[Requestor, PointEditor]:
        return None

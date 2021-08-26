from typing import Optional

from notion_py.interface.client.parse import BlockContentsParser
from notion_py.interface.struct import ValueCarrier


class BlockContents(ValueCarrier):
    def __init__(self):
        self.read: Optional[BlockContentsParser] = None
        self._overwrite = True

    def unpack(self) -> dict:
        pass

    def fetch(self, value: BlockContentsParser):
        self.read = value

    def set_overwrite(self, value: bool):
        self._overwrite = value

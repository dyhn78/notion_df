from typing import Optional

from notion_py.gateway.parse import BlockChildParser
from notion_py.gateway.common import ValueCarrier


class BlockContents(ValueCarrier):
    def __init__(self):
        self.read: Optional[BlockChildParser] = None
        self._overwrite = True

    def apply(self) -> dict:
        pass

    def fetch(self, value: BlockChildParser):
        self.read = value

    def set_overwrite(self, value: bool):
        self._overwrite = value
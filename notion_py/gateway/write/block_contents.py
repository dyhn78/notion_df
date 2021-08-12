from typing import Optional

from ..parse import BlockChildParser
# from ..interface import Block
from ..structure import ValueCarrier


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

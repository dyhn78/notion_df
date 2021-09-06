from __future__ import annotations
from typing import Optional, Union

from .supported import DefaultBlock
from notion_py.interface.struct import Editor


class UnsupportedBlock(DefaultBlock):
    def __init__(self, block_id: str, caller: Optional[Editor] = None):
        super().__init__(block_id, caller)

    def sync_master_id(self):
        pass

    def read(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def read_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def preview(self):
        return {}

    def execute(self):
        return {}

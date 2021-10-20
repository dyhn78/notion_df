from typing import Union

from notion_py.interface.editor.struct import MasterEditor
from notion_py.interface.common.struct import Editor


class UnsupportedBlock(MasterEditor):
    def __init__(self, caller: Editor, block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller

    @property
    def master_name(self):
        return self.master_url

    def reads(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def reads_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def preview(self):
        return {}

    def execute(self):
        return {}

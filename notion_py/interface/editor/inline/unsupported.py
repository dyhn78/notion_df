from typing import Union

from notion_py.interface.editor.common.struct import MasterEditor, Editor


class UnsupportedBlock(MasterEditor):
    def __init__(self, caller: Editor, block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller

    @property
    def payload(self):
        return None

    def save_required(self) -> bool:
        return False

    @property
    def is_supported_type(self) -> bool:
        return False

    @property
    def master_name(self):
        return self.master_url

    def reads(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def reads_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def save(self):
        return {}

    def save_info(self):
        return {}

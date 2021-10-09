from typing import Union

from notion_py.interface.struct import MasterEditor, PointEditor, Editor


class UnsupportedBlock(MasterEditor):
    def __init__(self, caller: Union[PointEditor, Editor], block_id: str):
        super().__init__(caller, block_id)

    @property
    def master_name(self):
        return self.master_url

    def fully_read(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def fully_read_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def make_preview(self):
        return {}

    def execute(self):
        return {}
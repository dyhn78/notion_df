from typing import Union

from ..base import Editor, MasterEditor, PayloadEditor


class UnsupportedBlock(MasterEditor):
    def __init__(self, caller: Editor, block_id: str):
        super().__init__(caller)
        self.caller = caller
        self._payload = UnsupportedPayload(self, block_id)

    @property
    def payload(self):
        return self._payload

    @property
    def block_name(self):
        return self.block_url

    @property
    def is_supported_type(self) -> bool:
        return False

    def reads(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.block_url}

    def reads_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.block_url}

    def save(self):
        return {}

    def save_info(self):
        return {}

    def save_required(self) -> bool:
        return False


class UnsupportedPayload(PayloadEditor):
    def save(self):
        return {}

    def save_info(self):
        return {}

    def save_required(self) -> bool:
        return False

    @property
    def can_have_children(self) -> bool:
        return False

from typing import Any

from ..structs.leaders import Registry, Block, Payload


class UnsupportedBlock(Block):
    def __init__(self, caller: Registry, id_or_url: str):
        super().__init__(caller, id_or_url)
        self.caller = caller

        self._payload = UnsupportedBlockPayload(self, id_or_url)

    @property
    def payload(self):
        return self._payload

    @property
    def block_name(self):
        return self.block_url

    def read(self) -> dict[str, Any]:
        return super().read()

    def richly_read(self) -> dict[str, Any]:
        return super().richly_read()

    @property
    def is_supported_type(self) -> bool:
        return False

    def save(self):
        return {}

    def save_info(self):
        return {}

    def save_required(self) -> bool:
        return False


class UnsupportedBlockPayload(Payload):
    def save(self):
        return {}

    def save_info(self):
        return {}

    def save_required(self) -> bool:
        return False

    @property
    def can_have_children(self) -> bool:
        return False

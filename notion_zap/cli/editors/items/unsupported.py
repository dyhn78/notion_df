from typing import Any

from ..structs.base_logic import AccessPoint
from ..structs.block_main import Block, Payload


class UnsupportedBlock(Block):
    def __init__(self, caller: AccessPoint, id_or_url: str):
        super().__init__(caller, id_or_url)

    def _initalize_payload(self) -> Payload:
        return UnsupportedPayload(self)

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


class UnsupportedPayload(Payload):
    def read(self) -> dict[str, Any]:
        return {}

    def richly_read(self) -> dict[str, Any]:
        return {}

    def save(self):
        return {}

    def save_info(self):
        return {}

    def save_required(self) -> bool:
        return False

    @property
    def can_have_children(self) -> bool:
        return False

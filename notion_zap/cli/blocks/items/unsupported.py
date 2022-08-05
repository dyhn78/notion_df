from typing import Any, Hashable

from ...core.base import Block, Space


# noinspection PyMethodMayBeStatic
class UnsupportedBlock(Block):
    def __init__(self, caller: Space, id_or_url: str, alias: Hashable = None):
        super().__init__(caller, id_or_url, alias)

    @property
    def block_name(self):
        return self.block_url

    @property
    def is_supported_type(self) -> bool:
        return False

    @property
    def can_have_children(self) -> bool:
        return False

    def read_contents(self) -> dict[str, Any]:
        return {}

    def richly_read_contents(self) -> dict[str, Any]:
        return {}

    def save(self):
        return {}

    def save_info(self):
        return {}

    def save_required(self) -> bool:
        return False

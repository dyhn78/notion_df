from typing import Any

from .main import Database
from ..structs.block_main import Payload


class DatabaseSchema(Payload):
    def __init__(self, caller: Database, block_id: str):
        super().__init__(caller, block_id)

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

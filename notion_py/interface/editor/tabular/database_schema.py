from .database import Database
from ..common.struct import PayloadEditor


class DatabaseSchema(PayloadEditor):
    def __init__(self, caller: Database, database_id: str):
        super().__init__(caller, database_id)

    def save_required(self) -> bool:
        pass

    def save_info(self):
        pass

    def save(self):
        pass

from .database_leaders import Database
from ..structs.leaders import Payload


class DatabaseSchema(Payload):
    def __init__(self, caller: Database, id_or_url: str):
        super().__init__(caller, id_or_url)

    def save_required(self) -> bool:
        pass

    def save_info(self):
        pass

    def save(self):
        pass

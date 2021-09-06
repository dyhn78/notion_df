from typing import Optional

from .pagelist import PageList
from ...api_format.parse import DatabaseParser
from ...gateway import RetrieveDatabase
from ...struct import MasterEditor, PropertyFrame, Editor, GroundEditor


class Database(MasterEditor):
    def __init__(self, database_id: str,
                 database_name: str,
                 frame: Optional[PropertyFrame] = None,
                 caller: Optional[Editor] = None):
        super().__init__(database_id, caller)
        self.frame = frame if frame else PropertyFrame()
        self.name = database_name
        self.yet_not_created = False
        self.pagelist = PageList(self, self.frame)
        self.agents.update(pagelist=self.pagelist)

    def sync_master_id(self):
        self.pagelist.sync_master_id()

    def retrieve(self):
        gateway = RetrieveDatabase(self.master_id)
        response = gateway.execute()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)

    def preview(self):
        return {**self.pagelist.preview()}

    def execute(self):
        if self.yet_not_created:
            self.pagelist.sync_master_id()
        self.pagelist.execute()


class DatabaseSchema(GroundEditor):
    pass  # TODO, in the far future

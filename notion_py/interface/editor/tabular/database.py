from typing import Union, Optional

from .pagelist import PageList
from notion_py.interface.api_parse import DatabaseParser
from notion_py.interface.gateway import RetrieveDatabase
from notion_py.interface.struct import MasterEditor, PointEditor, Editor, PropertyFrame


class Database(MasterEditor):
    def __init__(self, caller: Union[PointEditor, Editor],
                 database_id: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller, database_id)
        self.frame = frame if frame else PropertyFrame()
        self.alias = database_alias
        self.pagelist = PageList(self)
        self.agents.update(pagelist=self.pagelist)

    @property
    def master_name(self):
        return self.alias

    def retrieve(self):
        gateway = RetrieveDatabase(self)
        response = gateway.execute()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)

    def preview(self):
        return {**self.pagelist.preview()}

    def execute(self):
        self.pagelist.execute()

    def fully_read_rich(self):
        pass

    def fully_read(self):
        pass

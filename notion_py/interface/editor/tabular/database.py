from typing import Union, Optional

from ..abs_supported.abs_child_bearing import \
    BlockSphereCreator, BlockSphereUpdater
from ..struct import MasterEditor
from ...common.struct import AbstractRootEditor
from notion_py.interface.common import PropertyFrame
from notion_py.interface.parser import DatabaseParser
from notion_py.interface.requestor import RetrieveDatabase


class Database(MasterEditor):
    def __init__(self, caller: Union[AbstractRootEditor,
                                     BlockSphereUpdater,
                                     BlockSphereCreator],
                 database_id: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        from .pagelist import PageList
        super().__init__(caller, database_id)
        self.caller = caller
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

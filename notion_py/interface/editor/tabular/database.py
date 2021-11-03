from typing import Union, Optional

from notion_py.interface.common import PropertyFrame
from notion_py.interface.parser import DatabaseParser
from notion_py.interface.requestor import RetrieveDatabase
from ..common.with_children import ChildrenBearer, BlockChildren
from ..common.with_items import ItemsCreator, ItemsUpdater
from ..root_editor import RootEditor


class Database(ChildrenBearer):
    def __init__(self, caller: Union[RootEditor,
                                     ItemsUpdater,
                                     ItemsCreator],
                 database_id: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller)
        self.caller = caller
        self.frame = frame if frame else PropertyFrame()
        self.alias = database_alias

        from .database_schema import DatabaseSchema
        self.schema = DatabaseSchema(self, database_id)

        from .pagelist import PageList
        self.pagelist = PageList(self)

    @property
    def payload(self):
        return self.schema

    @property
    def children(self) -> BlockChildren:
        return self.pagelist

    def save_required(self) -> bool:
        return (self.payload.save_required()
                or self.children.save_required())

    @property
    def block_name(self):
        return self.alias

    def retrieve(self):
        gateway = RetrieveDatabase(self)
        response = gateway.execute()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)

    def save_info(self):
        return {**self.pagelist.save_info()}

    def save(self):
        self.pagelist.save()

    def reads(self):
        return {'pagelist': self.pagelist.by_title}

    def reads_rich(self):
        return self.reads()

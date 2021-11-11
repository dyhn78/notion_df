from typing import Union, Optional

from notion_zap.cli.gateway import parsers, requestors
from notion_zap.cli.struct import PropertyFrame
from ..common.with_children import ChildrenBearer, BlockChildren
from ..common.with_items import ItemAttachments
from notion_zap.cli.editors.root_editor import RootEditor


class Database(ChildrenBearer):
    def __init__(self, caller: Union[RootEditor, ItemAttachments],
                 database_id: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller)
        self.caller = caller
        self.frame = frame if frame else PropertyFrame()
        self.alias = database_alias
        self.root.by_alias[self.alias] = self

        from .database_schema import DatabaseSchema
        self.schema = DatabaseSchema(self, database_id)

        from .pagelist import PageList
        self._pagelist = PageList(self)

    @property
    def payload(self):
        return self.schema

    @property
    def pagelist(self):
        return self._pagelist

    @property
    def pl(self):
        return self.pagelist

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
        gateway = requestors.RetrieveDatabase(self)
        response = gateway.execute()
        parser = parsers.DatabaseParser(response)
        self.frame.fetch_parser(parser)

    def save_info(self):
        return {**self.pagelist.save_info()}

    def save(self):
        self.pagelist.save()

    def reads(self):
        return {'pagelist': self.pagelist.by_title}

    def reads_rich(self):
        return self.reads()

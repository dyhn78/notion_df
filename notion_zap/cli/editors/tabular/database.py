from typing import Union, Optional

from notion_zap.cli.gateway import parsers, requestors
from notion_zap.cli.struct import PropertyFrame
from ..common.with_children import ChildrenBearer, BlockChildren
from ..common.with_items import ItemChildren
from notion_zap.cli.editors.root_editor import RootEditor


class Database(ChildrenBearer):
    def __init__(self, caller: Union[RootEditor, ItemChildren],
                 id_or_url: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller)
        self.caller = caller
        self.frame = frame if frame else PropertyFrame()

        from .database_schema import DatabaseSchema
        self.schema = DatabaseSchema(self, id_or_url)

        from .pagelist import PageList
        self._pages = PageList(self)

        self.alias = database_alias
        self.root.by_alias[self.alias] = self

    def _fetch_children(self, request_size=0):
        """randomly query with the amount of <request_size>."""
        query = self.pages.open_query()
        query.execute(request_size)

    @property
    def payload(self):
        return self.schema

    @property
    def pages(self):
        return self._pages

    @property
    def children(self) -> BlockChildren:
        return self.pages

    def save_required(self) -> bool:
        return (self.payload.save_required()
                or self.children.save_required())

    @property
    def block_name(self):
        return self.alias

    def retrieve(self):
        requestor = requestors.RetrieveDatabase(self)
        response = requestor.execute_silent()
        parser = parsers.DatabaseParser(response)
        self.frame.fetch_parser(parser)
        requestor.print_comments()

    def save_info(self):
        return {**self.pages.save_info()}

    def save(self):
        self.pages.save()

    def reads(self):
        return {'pagelist': self.pages.by_title}

    def reads_rich(self):
        return self.reads()

import os
from pprint import pprint
from typing import Optional

from notion_client import Client, AsyncClient

from .inline.core import TextBlock, InlinePageBlock
from .tabular import Database, TabularPageBlock
from ..gateway import Query
from ..struct import MasterEditor, PropertyFrame, PropertyUnit, DateFormat
from ..struct.editor import AbstractRootEditor


class RootEditor(AbstractRootEditor):
    def __init__(self, async_client=False):
        super().__init__()
        self.top_documents: list[MasterEditor] = []
        if async_client:
            self.notion = AsyncClient(auth=self.token)
        else:
            self.notion = Client(auth=self.token)

    def __bool__(self):
        return any([bool(document) for document in self.top_documents])

    @property
    def token(self):
        return os.environ['NOTION_TOKEN'].strip("'").strip('"')

    def preview(self, pprint_this=True):
        preview = [document.preview() for document in self.top_documents]
        if pprint_this:
            pprint(preview)
        return preview

    def execute(self):
        for document in self.top_documents:
            document.execute()

    def open_database(self, database_id: str,
                      database_alias='',
                      frame: Optional[PropertyFrame] = None):
        document = Database(self, database_id, database_alias, frame)
        self.top_documents.append(document)
        return document

    def open_tabular_page(self, page_id: str,
                          frame: Optional[PropertyFrame] = None):
        document = TabularPageBlock(self, page_id, frame)
        self.top_documents.append(document)
        return document

    def open_inline_page(self, page_id: str):
        document = InlinePageBlock(self, page_id)
        self.top_documents.append(document)
        return document

    def open_text_block(self, block_id: str):
        document = TextBlock(self, block_id)
        self.top_documents.append(document)
        return document


class TypeName:
    database = Database
    tabular_page = TabularPageBlock
    inline_page = InlinePageBlock
    text_block = TextBlock

    query = Query

    date_format = DateFormat
    prop_frame = PropertyFrame
    prop_unit = PropertyUnit

import os
from pprint import pprint
from typing import Optional

from notion_client import Client, AsyncClient

from ..common import PropertyFrame
from ..common.struct import Editor
from ..utility import page_url_to_id
from .struct import MasterEditor
from .inline.text_block import TextBlock
from .inline.page_block import InlinePageBlock
from .tabular.database import Database
from .tabular.page import TabularPageBlock


class RootEditor(Editor):
    def __init__(self, async_client=False):
        super().__init__(root_editor=self)
        if async_client:
            self.notion = AsyncClient(auth=self.token)
        else:
            self.notion = Client(auth=self.token)
        self.top_editors: list[MasterEditor] = []
        self.by_id: dict[str, MasterEditor] = {}
        self.enable_overwrite = True

    def has_updates(self):
        return any([bool(editor) for editor in self.top_editors])

    def ids(self):
        return self.by_id.keys()

    def open_text_block(self, id_or_url: str):
        block_id = page_url_to_id(id_or_url)
        editor = TextBlock(self, block_id)
        self.top_editors.append(editor)
        return editor

    def preview(self, pprint_this=True):
        preview = [editor.preview() for editor in self.top_editors]
        if pprint_this:
            pprint(preview)
        return preview

    def execute(self):
        for editor in self.top_editors:
            editor.execute()

    def open_database(self, database_alias: str, id_or_url: str,
                      frame: Optional[PropertyFrame] = None):
        database_id = page_url_to_id(id_or_url)
        database = Database(self, database_id, database_alias, frame)
        self.top_editors.append(database)
        return database

    def open_pagelist(self, database_alias: str, id_or_url: str,
                      frame: Optional[PropertyFrame] = None):
        database = self.open_database(database_alias, id_or_url, frame)
        pagelist = database.pagelist
        return pagelist

    def open_tabular_page(self, id_or_url: str,
                          frame: Optional[PropertyFrame] = None):
        page_id = page_url_to_id(id_or_url)
        page = TabularPageBlock(self, page_id, frame)
        self.top_editors.append(page)
        return page

    def open_inline_page(self, id_or_url: str):
        page_id = page_url_to_id(id_or_url)
        page = InlinePageBlock(self, page_id)
        self.top_editors.append(page)
        return page

    @property
    def token(self):
        return os.environ['NOTION_TOKEN'].strip("'").strip('"')

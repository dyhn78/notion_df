import os
from collections import defaultdict
from pprint import pprint
from typing import Optional

from notion_client import Client, AsyncClient

from notion_zap.cli.struct import PropertyFrame
from notion_zap.cli.utility import page_url_to_id, stopwatch
from .base import Editor, MasterEditor


class RootEditor(Editor):
    def __init__(
            self,
            async_client=False,
            exclude_archived=False,
            disable_overwrite=False,
            emptylike_strings=None,
    ):
        super().__init__(root_editor=self)
        if async_client:
            client = AsyncClient(auth=self.token)
        else:
            client = Client(auth=self.token)
        self.client = client

        self._top_editors: list[MasterEditor] = []
        self._by_id = {}
        self._by_title = defaultdict(list)
        self._by_alias = {}

        # global settings, will be applied uniformly to all child-editors.
        self.disable_overwrite = disable_overwrite
        self.exclude_archived = exclude_archived
        if emptylike_strings is None:
            emptylike_strings = ['', '.', '-', '0', '1', 'None', 'False', '[]', '{}']
        self.emptylike_strings = emptylike_strings

    def is_emptylike(self, value):
        return str(value) in self.emptylike_strings

    @property
    def by_id(self) -> dict[str, MasterEditor]:
        return self._by_id

    def ids(self):
        return self.by_id.keys()

    @property
    def by_title(self) -> dict[str, list[MasterEditor]]:
        return self._by_title

    @property
    def by_alias(self) -> dict[str, MasterEditor]:
        return self._by_alias

    @property
    def databases(self):
        return self._by_alias.values()

    def save_required(self):
        return any([editor.save_required() for editor in self._top_editors])

    def save_info(self, pprint_this=True):
        preview = [editor.save_info() for editor in self._top_editors]
        if pprint_this:
            pprint(preview)
        return preview

    def save(self):
        for editor in self._top_editors:
            editor.save()
        stopwatch('작업 완료')

    def open_database(self, database_alias: str, id_or_url: str,
                      frame: Optional[PropertyFrame] = None):
        from . import Database
        database_id = page_url_to_id(id_or_url)
        database = Database(self, database_id, database_alias, frame)
        self._top_editors.append(database)
        return database

    def open_page_row(self, id_or_url: str,
                      frame: Optional[PropertyFrame] = None):
        from . import PageRow
        page_id = page_url_to_id(id_or_url)
        page = PageRow(self, page_id, frame=frame)
        self._top_editors.append(page)
        return page

    def open_page_item(self, id_or_url: str):
        from . import PageItem
        page_id = page_url_to_id(id_or_url)
        page = PageItem(self, page_id)
        self._top_editors.append(page)
        return page

    def open_text_item(self, id_or_url: str):
        from . import TextItem
        block_id = page_url_to_id(id_or_url)
        editor = TextItem(self, block_id)
        self._top_editors.append(editor)
        return editor

    @property
    def token(self):
        return os.environ['NOTION_TOKEN'].strip("'").strip('"')

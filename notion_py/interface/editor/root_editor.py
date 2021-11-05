import os
from collections import defaultdict
from pprint import pprint
from typing import Optional

from notion_client import Client, AsyncClient

from notion_py.interface.common import PropertyFrame
from notion_py.interface.utility import page_url_to_id, stopwatch
from .common.struct import MasterEditor, Editor


class RootEditor(Editor):
    def __init__(self, async_client=False):
        super().__init__(root_editor=self)
        if async_client:
            self.notion = AsyncClient(auth=self.token)
        else:
            self.notion = Client(auth=self.token)
        self._top_editors: list[MasterEditor] = []
        self._by_id = {}
        self._by_title = defaultdict(list)
        self._by_alias = {}

        # TODO : settings 클래스로 분리, 각각을 property 로 표현.
        # these settings applies uniformly to all sub-editors.
        self.enable_overwrite = True
        self.exclude_archived = False

    @property
    def by_id(self) -> dict[str, MasterEditor]:
        return self._by_id

    @property
    def by_title(self) -> dict[str, list[MasterEditor]]:
        return self._by_title

    @property
    def by_alias(self) -> dict[str, MasterEditor]:
        return self._by_alias

    def save_required(self):
        return any([bool(editor) for editor in self._top_editors])

    def ids(self):
        return self.by_id.keys()

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
        from .tabular.database import Database
        database_id = page_url_to_id(id_or_url)
        database = Database(self, database_id, database_alias, frame)
        self._top_editors.append(database)
        return database

    def open_tabular_page(self, id_or_url: str,
                          frame: Optional[PropertyFrame] = None):
        from .tabular.page_row import PageRow
        page_id = page_url_to_id(id_or_url)
        page = PageRow(self, page_id, frame=frame)
        self._top_editors.append(page)
        return page

    def open_inline_page(self, id_or_url: str):
        from .inline.page_item import PageItem
        page_id = page_url_to_id(id_or_url)
        page = PageItem(self, page_id)
        self._top_editors.append(page)
        return page

    def open_text_block(self, id_or_url: str):
        from .inline.text_item import TextItem
        block_id = page_url_to_id(id_or_url)
        editor = TextItem(self, block_id)
        self._top_editors.append(editor)
        return editor

    @property
    def token(self):
        return os.environ['NOTION_TOKEN'].strip("'").strip('"')

    @property
    def master(self):
        return self

    @property
    def parent(self):
        return self

    @property
    def entry_ancestor(self):
        return self


class RootEditorSettings:
    pass

from __future__ import annotations

import os
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from pprint import pprint
from typing import Union, Any, Optional
import datetime as dt

from notion_client import AsyncClient, Client

from notion_zap.cli.struct import DateFormat, PropertyFrame
from notion_zap.cli.utility import id_to_url, url_to_id, stopwatch


class Editor(metaclass=ABCMeta):
    def __init__(self, caller: Union[Editor]):
        self.caller = caller

    @property
    def root(self):
        return self.caller.root

    @abstractmethod
    def save_required(self) -> bool:
        pass

    @abstractmethod
    def save_info(self):
        pass

    def save_preview(self, **kwargs):
        pprint(self.save_info(), **kwargs)

    @abstractmethod
    def save(self):
        pass

    @property
    def master(self) -> MasterEditor:
        return self.caller.master

    @property
    def block_id(self) -> str:
        return self.master.block_id

    @property
    def block_url(self):
        return id_to_url(self.block_id)

    @property
    def block_name(self) -> str:
        return self.master.block_name

    @property
    def parent(self):
        """if the master is directly called by RootEditor, this will return None."""
        return self.master.parent

    @property
    def parent_id(self) -> str:
        return self.master.parent_id

    @property
    def archived(self):
        return self.master.archived


class AttachmentsEditor(Editor):
    @abstractmethod
    def attach(self, child: MasterEditor):
        pass

    @abstractmethod
    def detach(self, child: MasterEditor):
        pass


class RootEditor(AttachmentsEditor):
    def __init__(
            self,
            async_client=False,
            exclude_archived=False,
            disable_overwrite=False,
            customized_emptylike_strings=None,
            # enable_overwrite_by_same_value=False,
    ):
        Editor.__init__(self, self)
        if async_client:
            client = AsyncClient(auth=self.token)
        else:
            client = Client(auth=self.token)
        self.client = client

        self._stems: list[MasterEditor] = []
        self._by_id = {}
        self._by_title = defaultdict(list)

        from .. import Database
        self._by_alias: dict[Any, Database] = {}

        # global settings, will be applied uniformly to all child-editors.
        self.exclude_archived = exclude_archived
        self.disable_overwrite = disable_overwrite
        if customized_emptylike_strings is None:
            customized_emptylike_strings = \
                ['', '.', '-', '0', '1', 'None', 'False', '[]', '{}']
        self.emptylike_strings = customized_emptylike_strings
        # self.enable_overwrite_by_same_value = enable_overwrite_by_same_value

        # TODO : (1) enum 이용, (2) 실제로 requestor에 작동하는 로직 마련.
        self._log_succeed_request = False
        self._log_failed_request = True

    def set_logging__silent(self):
        self._log_succeed_request = False
        self._log_failed_request = False

    def set_logging__error(self):
        self._log_succeed_request = False
        self._log_failed_request = True

    def set_logging__all(self):
        self._log_succeed_request = True
        self._log_failed_request = True

    @property
    def root(self):
        return self

    @property
    def token(self):
        return os.environ['NOTION_TOKEN'].strip("'").strip('"')

    def is_emptylike(self, value):
        if isinstance(value, DateFormat):
            return value.is_emptylike()
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
    def by_alias(self):
        return self._by_alias

    @property
    def favorites(self):
        return self._by_alias.values()

    def attach(self, block: MasterEditor):
        self._stems.append(block)

    def detach(self, block: MasterEditor):
        self._stems.remove(block)

    def open_database(self, database_alias: str, id_or_url: str,
                      frame: Optional[PropertyFrame] = None):
        from .. import Database
        database = Database(self, id_or_url, database_alias, frame)
        self._stems.append(database)
        return database

    def open_page_row(self, id_or_url: str,
                      frame: Optional[PropertyFrame] = None):
        from .. import PageRow
        page = PageRow(self, id_or_url, frame=frame)
        self._stems.append(page)
        return page

    def open_page_item(self, id_or_url: str):
        from .. import PageItem
        page = PageItem(self, id_or_url)
        self._stems.append(page)
        return page

    def open_text_item(self, id_or_url: str):
        from .. import TextItem
        editor = TextItem(self, id_or_url)
        self._stems.append(editor)
        return editor

    def save_required(self):
        return any([editor.save_required() for editor in self._stems])

    def save_info(self, pprint_this=True):
        preview = [editor.save_info() for editor in self._stems]
        if pprint_this:
            pprint(preview)
        return preview

    def save(self):
        for editor in self._stems:
            editor.save()
        stopwatch('작업 완료')


class MasterEditor(Editor):
    def __init__(self, caller: AttachmentsEditor, id_or_url: str):
        super().__init__(caller)
        self.caller = caller
        self.__block_id = url_to_id(id_or_url)
        self.caller.attach(self)
        """
        1. declare payload, make the payload "register" to the attachment.
        this allows to search specific page from them. (.by_id, .by_title)
        2. "attach" the master to caller.
        this is required to exhaustive, trickle-down saving measures.
        """

    @property
    @abstractmethod
    def is_supported_type(self) -> bool:
        pass

    @property
    @abstractmethod
    def payload(self) -> PayloadEditor:
        pass

    @property
    def created_time(self):
        return self.payload.created_time

    @property
    def last_edited_time(self):
        return self.payload.last_edited_time

    @property
    def archived(self):
        return self.payload.archived

    @property
    def has_children(self) -> bool:
        return self.payload.has_children

    @property
    def can_have_children(self) -> bool:
        return self.payload.can_have_children

    @property
    def master(self):
        return self

    @property
    def block_id(self):
        try:
            return self.payload.block_id
        except AttributeError:
            # this happens before payload is declared
            return self.__block_id

    @property
    @abstractmethod
    def block_name(self):
        pass

    @property
    def parent(self):
        """if the master is directly called by RootEditor, this will return None."""
        if self.caller == self.root:
            return None
        parent = self.caller.master
        from ..common.with_children import ChildrenBearer
        assert isinstance(parent, ChildrenBearer)
        return parent

    @property
    def parent_id(self):
        from ..common.with_children import ChildrenBearer
        parent = self.parent
        try:
            assert isinstance(parent, ChildrenBearer)
            return self.parent.block_id
        except AssertionError:
            from notion_zap.cli.editors.editor_exceptions import NoParentFoundError
            raise NoParentFoundError(self.master)

    @property
    def entry_ancestor(self):
        if not self.block_id:
            return self.parent.entry_ancestor
        return self

    @abstractmethod
    def reads(self):
        pass

    @abstractmethod
    def reads_rich(self):
        pass

    @abstractmethod
    def save_info(self):
        """ example:
        {'contents': "unpack contents here",
         'children': "unpack children here"}
        """

    @abstractmethod
    def save(self):
        """
        1. since self.children go first than self.new_children,
            saving a multi-rank structure will be executed top to bottom,
            regardless of indentation.
        2. the 'ground editors', self.contents or self.tabular,
            have to refer to self.block_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the master deals with its reset task instead.
        """


class PayloadEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: MasterEditor, id_or_url: str):
        super().__init__(caller)
        self.__block_id = ''
        self._set_block_id(url_to_id(id_or_url))
        self._archived = None
        self._created_time = None
        self._last_edited_time = None

        self._has_children = None
        self._can_have_children = None

    @property
    def created_time(self) -> dt.datetime:
        return self._created_time

    @property
    def last_edited_time(self) -> dt.datetime:
        return self._last_edited_time

    @property
    def archived(self):
        return False if self._archived is None else self._archived

    @property
    def has_children(self):
        return self.can_have_children \
            if self._has_children is None else self._has_children

    @property
    def can_have_children(self):
        return True \
            if self._can_have_children is None else self._can_have_children

    @property
    def block_id(self) -> str:
        return self.__block_id

    def _set_block_id(self, value):
        self._unregister_id()
        self.__block_id = value
        self._register_id()

    def unregister_all(self):
        self._unregister_id()

    def _register_id(self):
        if self.block_id == '':
            return
        # register to root
        register_point = self.root.by_id
        register_point[self.block_id] = self.master
        # register to parent
        if self.parent is not None:
            register_point = self.parent.children.by_id
            register_point[self.block_id] = self.master

    def _unregister_id(self):
        if self.block_id == '':
            return
        # detach from root
        register_point = self.root.by_id
        register_point.pop(self.block_id)
        # detach from parent
        if self.parent is not None:
            register_point = self.parent.children.by_id
            register_point.pop(self.block_id)

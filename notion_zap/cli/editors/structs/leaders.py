from __future__ import annotations
import os
import datetime as dt
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from pprint import pprint
from typing import Any, Optional

from notion_client import AsyncClient, Client

from notion_zap.cli.struct import DateFormat, PropertyFrame
from notion_zap.cli.utility import id_to_url, url_to_id, stopwatch


class GeneralEditor(metaclass=ABCMeta):
    @property
    @abstractmethod
    def root(self) -> Root:
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def save_info(self):
        pass

    def save_preview(self, **kwargs):
        pprint(self.save_info(), **kwargs)

    @abstractmethod
    def save_required(self) -> bool:
        pass


class GeneralAttachments(GeneralEditor):
    def __init__(self):
        self.__by_id = {}
        self.__by_title = defaultdict(list)

    @abstractmethod
    def attach(self, child: Block):
        if child.caller != self:
            child.caller.detach(child)
        child.caller = self
        # fill the attach method here.

    @abstractmethod
    def detach(self, child: Block):
        from .exceptions import DanglingBlockError
        from ..common.pages import PageBlock
        if child.block_id:
            try:
                self.by_id.pop(child.block_id)
            except KeyError:
                raise DanglingBlockError(child, self)
        if isinstance(child, PageBlock) and child.title:
            try:
                self.by_title[child.title].remove(child)
            except ValueError:
                raise DanglingBlockError(child, self)

    @property
    def by_id(self) -> dict[str, Block]:
        """this will be maintained from childrens' side."""
        return self.__by_id

    def ids(self):
        return self.by_id.keys()

    @property
    def by_title(self) -> dict[str, list[Block]]:
        """this will be maintained from childrens' side."""
        return self.__by_title


class Root(GeneralAttachments):
    def __init__(
            self,
            async_client=False,
            exclude_archived=False,
            disable_overwrite=False,
            customized_emptylike_strings=None,
            # enable_overwrite_by_same_value=False,
    ):
        super().__init__()
        if async_client:
            client = AsyncClient(auth=self.token)
        else:
            client = Client(auth=self.token)
        self.client = client

        self._stems: list[Block] = []

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
    def by_alias(self):
        return self._by_alias

    @property
    def aliased_blocks(self):
        return self._by_alias.values()

    def attach(self, child: Block):
        super().attach(child)
        self._stems.append(child)

    def detach(self, child: Block):
        super().detach(child)
        self._stems.remove(child)

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


class Editor(GeneralEditor, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, caller: GeneralEditor):
        self.caller = caller

    @property
    def root(self):
        return self.caller.root

    @property
    @abstractmethod
    def master(self) -> Block:
        pass

    @property
    def block_id(self) -> str:
        return self.master.block_id

    @property
    def block_name(self) -> str:
        return self.master.block_name

    @property
    def block_url(self):
        return id_to_url(self.block_id)

    @property
    def parent(self):
        """return None if block_master is directly called from the root."""
        attach_point = self.master.caller
        if isinstance(attach_point, Editor):
            parent = attach_point.master
            from ..common.with_children import ChildrenBearer
            if not isinstance(parent, ChildrenBearer):
                from .exceptions import InvalidParentTypeError
                raise InvalidParentTypeError(self.master)
            return parent
        return None

    @property
    def parent_id(self) -> Optional[str]:
        """return None if the block has no parent.
        don't confuse with the empty string(''),
        which means the parent is yet-not-created at the server."""
        if self.parent:
            return self.parent.block_id

    @property
    def entry_ancestor(self):
        if not self.block_id:
            if not self.parent:
                from .exceptions import NoParentFoundError
                raise NoParentFoundError(self.master)
            return self.parent.entry_ancestor
        return self.master

    @property
    def archived(self):
        return self.master.archived

    @abstractmethod
    def read(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def richly_read(self) -> dict[str, Any]:
        pass


class Block(Editor):
    def __init__(self, caller: GeneralAttachments, id_or_url: str):
        self.caller = caller
        self.__block_id = url_to_id(id_or_url)
        self.caller.attach(self)
        # Now declare payload here, make it "register" to the attachment.
        #  this allows to search specific page from them. (.by_id, .by_title)

    @property
    def master(self):
        return self

    @property
    def block_id(self):
        try:
            return self.payload.block_id
        except AttributeError:
            # this is needed to attach itself to parents' attachments
            #  before its payload is declared
            return self.__block_id

    @property
    @abstractmethod
    def block_name(self):
        pass

    @property
    @abstractmethod
    def is_supported_type(self) -> bool:
        pass

    @property
    @abstractmethod
    def payload(self) -> Payload:
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

    @abstractmethod
    def read(self) -> dict[str, Any]:
        return {'type': type(self).__name__,
                'id': self.block_id}

    @abstractmethod
    def richly_read(self) -> dict[str, Any]:
        return self.read()

    @abstractmethod
    def save_info(self):
        """ example:
        {'contents': "unpack contents here",
         'children': "unpack children here"}
        """
        return self.read()

    @abstractmethod
    def save(self):
        """
        1. since self.children go first than self.new_children,
            saving a multi-rank structure will be executed top to bottom,
            regardless of indentation.
        2. the 'ground editors', self.contents or self.props,
            have to refer to self.block_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the master deals with its reset task instead.
        """


class Follower(Editor, metaclass=ABCMeta):
    def __init__(self, caller: Editor):
        self.caller = caller

    @property
    def master(self) -> Block:
        return self.caller.master


class Payload(Follower, metaclass=ABCMeta):
    def __init__(self, caller: Block, id_or_url: str):
        super().__init__(caller)
        self.caller = caller
        self.__block_id = ''
        self._set_block_id(url_to_id(id_or_url))

        self._archived = None
        self._created_time = None
        self._last_edited_time = None
        self._has_children = None
        self._can_have_children = None

    @property
    def register_points(self) -> list[GeneralAttachments]:
        if self.root == self.caller.caller:
            attach_points = [self.root]
        else:
            attach_points = [self.root, self.caller.caller]
        return attach_points

    @property
    def block_id(self) -> str:
        return self.__block_id

    def _set_block_id(self, value: str):
        """set the value to empty string('') will unregister the block."""
        if self.__block_id:
            for attachments in self.register_points:
                if attachments.by_id[self.__block_id] == self.master:
                    attachments.by_id.pop(self.__block_id)
                else:
                    print(f'WARNING: {self.master} was not registered to {attachments}')
        self.__block_id = value
        if self.__block_id:
            for attachments in self.register_points:
                attachments.by_id[self.__block_id] = self.master

    @property
    def archived(self):
        if self._archived is not None:
            return self._archived
        else:
            return False

    @property
    def has_children(self):
        if self._has_children is not None:
            return self._has_children
        else:
            return self.can_have_children

    @property
    def can_have_children(self):
        if self._can_have_children is not None:
            return self._can_have_children
        else:
            return True

    @property
    def created_time(self) -> Optional[dt.datetime]:
        return self._created_time

    @property
    def last_edited_time(self) -> Optional[dt.datetime]:
        return self._last_edited_time

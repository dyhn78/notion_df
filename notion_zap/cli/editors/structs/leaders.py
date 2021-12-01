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


class Editor(metaclass=ABCMeta):
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


class Registry(Editor):
    def __init__(self):
        self.__by_id = {}
        self.__by_title = defaultdict(list)

    @abstractmethod
    def add_block(self, child: Block):
        if child.caller != self:
            child.caller.remove_block(child)
        child.caller = self
        # fill the rest here.

    @abstractmethod
    def remove_block(self, child: Block):
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
        # fill the rest here.

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


class Root(Registry):
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

    def add_block(self, child: Block):
        super().add_block(child)
        self._stems.append(child)

    def remove_block(self, child: Block):
        super().remove_block(child)
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


class BlockEditor(Editor, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, caller: Editor):
        self.caller = caller

    @property
    def root(self):
        return self.caller.root

    @property
    @abstractmethod
    def block(self) -> Block:
        pass

    @property
    @abstractmethod
    def block_id(self) -> str:
        pass

    @property
    @abstractmethod
    def block_name(self) -> str:
        pass

    @property
    @abstractmethod
    def archived(self):
        pass

    @property
    def block_url(self):
        return id_to_url(self.block_id)

    @property
    def parent(self):
        """return None if block_master is directly called from the root."""
        attach_point = self.block.caller
        if isinstance(attach_point, BlockEditor):
            parent = attach_point.block
            from ..common.with_children import ChildrenBearer
            if not isinstance(parent, ChildrenBearer):
                from .exceptions import InvalidParentTypeError
                raise InvalidParentTypeError(self.block)
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
                raise NoParentFoundError(self.block)
            return self.parent.entry_ancestor
        return self.block

    @abstractmethod
    def read(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def richly_read(self) -> dict[str, Any]:
        pass


class Block(BlockEditor):
    def __init__(self, caller: Registry, id_or_url: str):
        self.caller = caller
        self.__block_id = url_to_id(id_or_url)
        self.caller.add_block(self)
        # Now declare payload here, make it "register" to the attachment.
        #  this allows to search specific page from them. (.by_id, .by_title)

    @property
    def _registries(self) -> list[Registry]:
        if self.root == self.caller:
            registry = [self.root]
        else:
            registry = [self.root, self.caller]
        return registry

    def attach_to(self, register: Registry):
        if register != self.caller:
            self.detach_from(self.caller)
            self.caller = register
        self.caller.add_block(self)

    def detach_from(self, register: Registry):
        from .exceptions import DanglingBlockError
        if self.block_id:
            try:
                register.by_id.pop(self.block_id)
            except KeyError:
                raise DanglingBlockError(self, register)

    def close(self):
        """use this to delete a wrong block
        (probably those with nonexisting block_id)"""
        for registry in self._registries:
            if registry.by_id[self.__block_id] == self.block:
                registry.by_id.pop(self.__block_id)
            else:
                from .exceptions import DanglingBlockError
                raise DanglingBlockError(self, registry)
        self.caller.remove_block(self)

    @property
    def block(self):
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

    @property
    def basic_info(self):
        return {'type': type(self).__name__,
                'id': self.block_id}

    @abstractmethod
    def read(self) -> dict[str, Any]:
        return self.basic_info

    @abstractmethod
    def richly_read(self) -> dict[str, Any]:
        return self.basic_info

    @abstractmethod
    def save_info(self):
        """ example:
        {'contents': "unpack contents here",
         'children': "unpack children here"}
        """
        pass

    @abstractmethod
    def save(self):
        """ remarks:
        1. since self.children go first than self.new_children,
            saving a multi-rank structure will be executed top to bottom,
            regardless of indentation.
        2. the 'ground editors', self.contents or self.props,
            have to refer to self.block_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the block deals with its reset task instead.
        """
        pass


class Follower(BlockEditor, metaclass=ABCMeta):
    def __init__(self, caller: BlockEditor):
        self.caller = caller

    @property
    def block(self) -> Block:
        return self.caller.block

    @property
    def block_id(self) -> str:
        return self.block.block_id

    @property
    def block_name(self) -> str:
        return self.block.block_name

    @property
    def archived(self):
        return self.block.archived


class Payload(BlockEditor, metaclass=ABCMeta):
    def __init__(self, caller: Block, id_or_url: str):
        super().__init__(caller)
        self.caller = caller
        self.__block_id = url_to_id(id_or_url)

        self._archived = None
        self._created_time = None
        self._last_edited_time = None
        self._has_children = None
        self._can_have_children = None

    @property
    def _registries(self) -> list[Registry]:
        if self.root == self.caller.caller:
            registry = [self.root]
        else:
            registry = [self.root, self.caller.caller]
        return registry

    @property
    def block(self) -> Block:
        return self.caller

    @property
    def block_id(self) -> str:
        return self.__block_id

    def _set_block_id(self, value: str):
        """set the value to empty string('') will unregister the block."""
        if self.__block_id:
            for attachments in self._registries:
                if attachments.by_id[self.__block_id] == self.block:
                    attachments.by_id.pop(self.__block_id)
                else:
                    print(f'WARNING: {self.block} was not registered to {attachments}')
        self.__block_id = value
        if self.__block_id:
            for attachments in self._registries:
                attachments.by_id[self.__block_id] = self.block

    @property
    def block_name(self) -> str:
        return self.block.block_name

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

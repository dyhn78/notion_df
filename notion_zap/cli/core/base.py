from __future__ import annotations

import datetime as dt
import os
from abc import ABCMeta, abstractmethod
from typing import Hashable, Union, Optional, Any, Iterable

from notion_client import AsyncClient, Client

from notion_zap.cli.core import PropertyFrame
from notion_zap.cli.core.mixins import Saveable
from notion_zap.cli.core.registry_table import IndexTable, ClassifyTable, RegistryTable
from notion_zap.cli.utility import id_to_url, url_to_id


class BaseComponent(metaclass=ABCMeta):
    @property
    @abstractmethod
    def root(self) -> Root:
        pass


class Registry(BaseComponent, metaclass=ABCMeta):
    def __init__(self):
        self.__by_id: IndexTable[str, Block] = IndexTable()
        self.__by_title: ClassifyTable[str, Block] = ClassifyTable()
        from notion_zap.cli.blocks import PageRow
        self.__by_keys: dict[str, RegistryTable[Hashable, PageRow]] = {}
        self.__by_tags: dict[Hashable, RegistryTable[Hashable, PageRow]] = {}

    def tables(self, key: Union[str, tuple]):
        if key == 'id':
            return self.by_id
        elif key == 'title':
            return self.by_title
        elif key[0] == 'key':
            return self.by_keys[key[1]]
        elif key[0] == 'tag':
            return self.by_tags[key[1]]
        raise ValueError(key)

    @property
    def by_id(self):
        """this will be maintained from childrens' side."""
        return self.__by_id

    def ids(self):
        return self.by_id.keys()

    @property
    def by_title(self):
        """this will be maintained from childrens' side."""
        return self.__by_title

    @property
    def by_keys(self):
        return self.__by_keys

    @property
    def by_tags(self):
        return self.__by_tags


class Component(BaseComponent, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, caller: BaseComponent):
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
    def is_archived(self):
        pass

    @property
    def block_url(self):
        return id_to_url(self.block_id)

    @property
    def parent(self):
        """return None if block_master is directly called from the root."""
        parents_registry = self.block.caller
        if isinstance(parents_registry, Component):
            parent = parents_registry.block
            from notion_zap.cli.blocks.shared.children import BlockWithChildren
            if not isinstance(parent, BlockWithChildren):
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


class Follower(Component):
    def __init__(self, caller: Component):
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
    def is_archived(self):
        return self.block.is_archived


class Block(Component, Saveable, metaclass=ABCMeta):
    def __init__(self, gatherer: Space, id_or_url: str, alias: Hashable = None):
        if getattr(self, '_block_id', None) is not None:
            return

        self._block_id = url_to_id(id_or_url)
        self._archived = None
        self._created_time = None
        self._last_edited_time = None
        self._has_children = None
        self._can_have_children = None

        self.caller = gatherer
        self.caller.contain(self)

        from notion_zap.cli.core.registerer import RegistererMap
        self._regs = RegistererMap(self)
        self._regs.add('id', lambda x: x.block_id)

        self._alias = None
        self.alias = alias

    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, alias: Hashable):
        if self._alias is not None:
            self.root.block_aliases.pop(self._alias)
        self._alias = alias
        if self._alias is not None:
            self.root.block_aliases[self._alias] = self

    def __repr__(self):
        if self.block_name:
            return f"{type(self).__name__.lower()} {self.block_name}"
        elif self.block_id:
            return f"{type(self).__name__.lower()} {self.block_url}"
        else:
            return f"new {type(self).__name__.lower()} at {hex(id(self))}"

    def __str__(self):
        if self.block_name:
            return self.block_name
        elif self.block_id:
            return self.block_url
        else:
            return f"new {type(self).__name__.lower()}"

    def move_to(self, new_caller: Space):
        if (prev := self.caller) != new_caller:
            prev.release(self)
            self._regs.un_register_from_parent()
            self.caller = new_caller
            new_caller.contain(self)
            self._regs.register_to_parent()

    def close(self):
        """use this method to detach a wrong block
        (probably due to nonexisting block_id)"""
        if isinstance(prev := self.caller, Space):
            prev.release(self)
            self._regs.un_register_from_root_and_parent()
        self.caller = None

    @property
    def block(self):
        return self

    @property
    def block_id(self):
        return self._block_id

    @property
    @abstractmethod
    def block_name(self):
        pass

    @property
    @abstractmethod
    def is_supported_type(self) -> bool:
        pass

    @property
    def is_archived(self):
        if self._archived is not None:
            return self._archived
        else:
            return False

    def archive(self):
        pass

    def un_archive(self):
        pass

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

    @property
    def basic_info(self):
        return {'type': type(self).__name__,
                'id': self.block_id}

    def read(self, max_rank_diff=0) -> dict[str, Any]:
        return dict(**self.basic_info,
                    contents=self.read_contents())

    def richly_read(self, max_rank_diff=0) -> dict[str, Any]:
        return dict(**self.basic_info,
                    contents=self.richly_read_contents())

    @abstractmethod
    def read_contents(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def richly_read_contents(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def save_info(self) -> dict[str, Any]:
        return self.basic_info

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


class Root(Registry):
    @property
    def token(self) -> str:
        return os.environ['NOTION_TOKEN'].strip("'").strip('"')

    def __init__(
            self,
            async_client=False,
            exclude_archived=False,
            disable_overwrite=False,
            customized_emptylike_strings=None,
            print_response_heads=0,
            print_request_formats=False,
            # enable_overwrite_by_same_value=False,
    ):
        super().__init__()
        if async_client:
            client = AsyncClient(auth=self.token)
        else:
            client = Client(auth=self.token)
        self.client = client

        self.space = RootSpace(self)

        self.block_aliases: dict[Any, Block] = {}

        # global settings, will be applied uniformly to all child-editors.
        self.exclude_archived = exclude_archived
        self.disable_overwrite = disable_overwrite
        if customized_emptylike_strings is None:
            customized_emptylike_strings = \
                ['', '.', '-', '0', '1', 'None', 'False', '[]', '{}']
        self.emptylike_strings = customized_emptylike_strings
        self.print_heads = print_response_heads
        self.print_request_formats = print_request_formats
        # self.enable_overwrite_by_same_value = enable_overwrite_by_same_value

    @property
    def root(self):
        return self

    def save(self):
        return self.space.save()

    def __getitem__(self, key: Hashable | Iterable[Hashable]):
        if isinstance(key, str):
            return self._get_item_by_single_key(key)
        if isinstance(key, Iterable):
            return self._get_item_by_multi_keys(key)
        return self._get_item_by_single_key(key)


    def _get_item_by_single_key(self, key: Hashable):
        try:
            return self.block_aliases[key]
        except KeyError:
            raise KeyError(key)

    def _get_item_by_multi_keys(self, keys: Iterable[Hashable]):
        return [self._get_item_by_single_key(key) for key in keys]

    def get_blocks(self, keys: Iterable[Hashable]):
        return [self[key] for key in keys]

    def eval_as_not_empty(self, value) -> bool:
        from notion_zap.cli.core.date_property_value import DatePropertyValue
        if isinstance(value, DatePropertyValue):
            return bool(value)
        return str(value) not in self.emptylike_strings


class RootSettings:
    def __init__(self):
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


class Space(Registry, Saveable, metaclass=ABCMeta):
    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def contain(self, block):
        """this will be called from child's side."""
        pass

    @abstractmethod
    def release(self, block):
        """this will be called from child's side."""
        pass

    @abstractmethod
    def read(self, max_rank_diff=0) -> dict[str, Any]:
        pass

    @abstractmethod
    def richly_read(self, max_rank_diff=0) -> dict[str, Any]:
        pass


class RootSpace(Space):
    def __init__(self, caller: Root):
        super().__init__()
        self.caller = caller

        self.direct_blocks: list[Block] = []

    def __iter__(self):
        return iter(self.direct_blocks)

    @property
    def root(self) -> Root:
        return self.caller

    def save(self):
        for block in self.direct_blocks:
            block.save()

    def save_info(self):
        return [block.save_info() for block in self.direct_blocks]

    def save_required(self):
        return any([block.save_required() for block in self.direct_blocks])

    def read(self, max_rank_diff=0) -> dict[str, Any]:
        return {'root': child.read(max_rank_diff) for child in self.direct_blocks}

    def richly_read(self, max_rank_diff=0) -> dict[str, Any]:
        return {'root': child.richly_read(max_rank_diff) for child in self.direct_blocks}

    def contain(self, block):
        self.direct_blocks.append(block)

    def release(self, block):
        self.direct_blocks.remove(block)

    def database(self, id_or_url: str, alias: Hashable = None, frame: PropertyFrame = None):
        from notion_zap.cli.blocks import Database
        block = Database(self, id_or_url, alias, frame)
        return block

    def page_row(self, id_or_url: str, alias: Hashable = None, frame: PropertyFrame = None):
        from notion_zap.cli.blocks import PageRow
        block = PageRow(self, id_or_url, alias, frame)
        return block

    def page_item(self, id_or_url: str, alias: Hashable = None):
        from notion_zap.cli.blocks import PageItem
        block = PageItem(self, id_or_url, alias)
        return block

    def text_item(self, id_or_url: str, alias: Hashable = None):
        from notion_zap.cli.blocks import TextItem
        block = TextItem(self, id_or_url, alias)
        return block

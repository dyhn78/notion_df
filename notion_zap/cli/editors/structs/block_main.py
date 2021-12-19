from __future__ import annotations

import datetime as dt
from abc import abstractmethod, ABCMeta
from typing import Optional, Any

from notion_zap.cli.utility import url_to_id, id_to_url
from .base_logic import Saveable, BaseComponent, Gatherer


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
    def archived(self):
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
            from notion_zap.cli.editors.structs.children import BlockWithChildren
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


class Block(Component, Saveable, metaclass=ABCMeta):
    def __init__(self, caller: Gatherer, id_or_url: str):
        self._block_id = url_to_id(id_or_url)
        self._archived = None
        self._created_time = None
        self._last_edited_time = None
        self._has_children = None
        self._can_have_children = None

        self.caller = caller
        self.caller.attach(self)

        if not getattr(self, 'regs', None):
            from .registerer import RegistererMap
            self.regs = RegistererMap(self)
            self.regs.add('id', lambda x: x.block_id)

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

    def close(self):
        """use this method to detach a wrong block
        (probably due to nonexisting block_id)"""
        if isinstance(prev := self.caller, Gatherer):
            prev.detach(self)
            self.regs.un_register_from_root_and_parent()
        self.caller = None

    def move_parent(self, new_gatherer: Gatherer):
        if (prev := self.caller) != new_gatherer:
            prev.detach(self)
            self.regs.un_register_from_parent()
            self.caller = new_gatherer
            new_gatherer.attach(self)
            self.regs.register_to_parent()

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
    def archived(self):
        return self.block.archived
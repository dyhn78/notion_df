from __future__ import annotations
import datetime as dt
from abc import abstractmethod, ABCMeta
from typing import Optional, Any

from notion_zap.cli.utility import url_to_id, id_to_url
from .base_logic import Readable, Saveable, BaseComponent, AccessPoint


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
            from ..common.with_children import BlockWithChildren
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


class Block(Component, Readable, Saveable, metaclass=ABCMeta):
    def __init__(self, caller: AccessPoint, id_or_url: str):
        self._temp_block_id = url_to_id(id_or_url)
        self._temp_caller = caller
        self.__payload = self._initalize_payload()
        self.__caller = None
        self.caller = self._temp_caller
        self._temp_block_id = None
        self._temp_caller = None

    @abstractmethod
    def _initalize_payload(self) -> Payload:
        pass

    @property
    def block(self):
        return self

    @property
    def block_id(self):
        try:
            return self.payload.block_id
        except AttributeError:
            # this temporary attribute is needed before the payload is declared
            return self._temp_block_id

    @property
    def caller(self) -> AccessPoint:
        try:
            return self.__caller
        except AttributeError:
            return self._temp_caller

    @caller.setter
    def caller(self, value: Optional[AccessPoint]):
        """assign the value to None to delete a wrong block
        (probably due to nonexisting block_id)"""
        prev = self.caller
        if (
                isinstance(prev, AccessPoint)
                and isinstance(value, AccessPoint)
                and prev != value
        ):
            prev.detach(self)
            self.regs.un_register_from_parent()
            self.__caller = value
            value.attach(self)
            self.regs.register_to_parent()
        elif isinstance(value, AccessPoint):
            self.__caller = value
            value.attach(self)
            # regs will register from payloads side.
        elif isinstance(prev, AccessPoint):
            prev.detach(self)
            self.regs.un_register_from_root_and_parent()

    @property
    def regs(self):
        return self.payload.regs

    @property
    @abstractmethod
    def block_name(self):
        pass

    @property
    @abstractmethod
    def is_supported_type(self) -> bool:
        pass

    @property
    def payload(self) -> Payload:
        return self.__payload

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


class Payload(Component, Readable, Saveable, metaclass=ABCMeta):
    def __init__(self, caller: Block):
        super().__init__(caller)
        self.caller = caller

        self._archived = None
        self._created_time = None
        self._last_edited_time = None
        self._has_children = None
        self._can_have_children = None
        from .registry_writer import Registrant, IdRegisterer
        self.__block_id = self.caller.block_id
        if not getattr(self, 'regs', None):
            self.regs = Registrant(self)
            id_reg = IdRegisterer(self)
            id_reg.register_to_root_and_parent()
            self.regs.add(id_reg)

    @property
    def block(self) -> Block:
        return self.caller

    @property
    def block_id(self) -> str:
        return self.__block_id

    def _set_block_id(self, value: str):
        self.regs['id'].un_register_from_root_and_parent()
        self.__block_id = value
        self.regs['id'].register_to_root_and_parent()

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

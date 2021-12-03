from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Any

from .block_main import Follower


class Registrant(Follower):
    def __init__(self, block):
        super().__init__(block)
        self._elements: dict[Any, Registerer] = {}

    def __iter__(self):
        return iter(self._elements.values())

    def __getitem__(self, key):
        try:
            return self._elements[key]
        except KeyError as e:
            raise KeyError(f"{e.args[0]} not in cluster :: "
                           f"{list(self._elements.keys())}")

    def add(self, value: Registerer):
        self._elements[value.track_key] = value

    def register_to_parent(self):
        for reg in self:
            reg.register_to_parent()

    def register_to_root_and_parent(self):
        for reg in self:
            reg.register_to_root_and_parent()

    def un_register_from_parent(self):
        for reg in self:
            reg.un_register_from_parent()

    def un_register_from_root_and_parent(self):
        for reg in self:
            reg.un_register_from_root_and_parent()


class Registerer(Follower, metaclass=ABCMeta):
    def __init__(self, caller):
        super().__init__(caller)

    @property
    @abstractmethod
    def track_key(self):
        pass

    @property
    @abstractmethod
    def track_val(self):
        pass

    @abstractmethod
    def register_to_parent(self):
        pass

    @abstractmethod
    def register_to_root_and_parent(self):
        pass

    @abstractmethod
    def un_register_from_parent(self):
        pass

    @abstractmethod
    def un_register_from_root_and_parent(self):
        pass


class IdRegisterer(Registerer):
    @property
    def track_key(self):
        return 'id'

    @property
    def track_val(self):
        return self.block_id

    def register_to_parent(self):
        if self.track_val:
            self.block.caller.by_id[self.track_val] = self.block

    def register_to_root_and_parent(self):
        self.register_to_parent()
        if self.track_val:
            self.root.by_id[self.track_val] = self.block

    def un_register_from_parent(self):
        from .exceptions import DanglingBlockError
        if self.track_val:
            try:
                self.block.caller.by_id.pop(self.track_val)
            except KeyError:
                raise DanglingBlockError(self.block, self.block.caller)

    def un_register_from_root_and_parent(self):
        from .exceptions import DanglingBlockError
        if self.track_val:
            try:
                self.root.by_id.pop(self.track_val)
            except KeyError:
                raise DanglingBlockError(self.block, self.root)

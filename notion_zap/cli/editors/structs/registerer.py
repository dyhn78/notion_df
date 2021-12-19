from __future__ import annotations
from abc import ABCMeta
from typing import Any, Callable, Union

from .block_main import Follower
from .exceptions import DanglingBlockError


class RegistererMap(Follower):
    def __init__(self, block):
        super().__init__(block)
        self._elements: dict[Any, Registerer] = {}

    def __iter__(self):
        return iter(self._elements.values())

    def __repr__(self):
        return str(self._elements)

    def __getitem__(self, key):
        try:
            return self._elements[key]
        except KeyError as e:
            raise KeyError(f"{e.args[0]} not in cluster :: "
                           f"{list(self._elements.keys())}")

    def add(self, track_key: Union[str, tuple],
            track_val: Callable[[Follower], Any]):
        reg = Registerer(self, track_key, track_val)
        self._elements[track_key] = reg
        # TODO: master-payload 통합하면 return 값 삭제
        return reg

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
    def __init__(self, caller,
                 track_key: Union[str, tuple],
                 track_val: Callable[[Follower], Any]):
        super().__init__(caller)
        self._track_key = track_key
        self._track_val = track_val
        # TODO: master-payload 통합하면 여기서 즉시 register_to_root_and_parent

    @property
    def track_key(self):
        return self._track_key

    @property
    def track_val(self):
        return self._track_val(self)

    @property
    def parents_table(self):
        return self.block.caller.tables(self.track_key)

    @property
    def roots_table(self):
        return self.root.tables(self.track_key)

    def register_to_parent(self):
        if self.track_val:
            self.parents_table.update({self.track_val: self.block})

    def register_to_root_and_parent(self):
        self.register_to_parent()
        if self.track_val:
            self.roots_table.update({self.track_val: self.block})

    def un_register_from_parent(self):
        if self.track_val:
            try:
                self.parents_table.remove({self.track_val: self.block})
            except KeyError:
                raise DanglingBlockError(self.block, self.block.caller)

    def un_register_from_root_and_parent(self):
        self.un_register_from_parent()
        if self.track_val:
            try:
                self.roots_table.remove({self.track_val: self.block})
            except KeyError:
                raise DanglingBlockError(self.block, self.root)

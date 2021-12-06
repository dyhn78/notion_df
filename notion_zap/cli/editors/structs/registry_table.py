from __future__ import annotations
from abc import abstractmethod
from collections import defaultdict
from itertools import chain
from typing import Hashable, MutableMapping, TypeVar

Block = TypeVar('Block')


class RegistryTable(MutableMapping[Hashable, Block]):
    def __init__(self, table: dict[Hashable, Block]):
        self._table = table
        self.pop = None

    def __delitem__(self, key: Hashable) -> None:
        del self._table[key]

    def __len__(self) -> int:
        return len(self._table)

    def __iter__(self):
        return iter(self._table.keys())

    @abstractmethod
    def update(self, mapping: dict[Hashable, Block], **kwargs: dict[Hashable, Block]):
        pass

    @abstractmethod
    def remove(self, mapping: dict[Hashable, Block], **kwargs: dict[Hashable, Block]):
        pass


class IndexTable(RegistryTable):
    def __init__(self):
        super().__init__({})

    def __getitem__(self, key: Hashable) -> Block:
        return self._table[key]

    def __setitem__(self, key: Hashable, value: Block):
        self._table[key] = value

    def update(self, mapping: dict[Hashable, Block], **kwargs: dict[Hashable, Block]):
        self._table.update(mapping)

    def remove(self, mapping: dict[Hashable, Block], **kwargs: dict[Hashable, Block]):
        for key, value in chain(mapping.items(), kwargs.items()):
            if self._table[key] == value:
                self._table.pop(key)


class ClassifyTable(RegistryTable):
    def __init__(self):
        super().__init__(defaultdict(list))

    def __getitem__(self, key: Hashable) -> list[Block]:
        return self._table[key]

    def __setitem__(self, key: Hashable, value: list[Block]):
        self._table[key] = value

    def update(self, mapping: dict[Hashable, Block], **kwargs: dict[Hashable, Block]):
        for key, value in mapping.items():
            self._table[key].append(value)

    def remove(self, mapping: dict[Hashable, Block], **kwargs: dict[Hashable, Block]):
        for key, value in mapping.items():
            if value in self._table[key]:
                self._table[key].remove(value)

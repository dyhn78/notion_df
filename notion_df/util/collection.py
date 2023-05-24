from __future__ import annotations

import inspect
from enum import Enum
from itertools import chain
from typing import TypeVar, Iterator, NewType, Sequence, overload, Iterable

from notion_df.util.exception import NotionDfKeyError, NotionDfIndexError, NotionDfTypeError
from notion_df.util.misc import repr_object


class StrEnum(str, Enum):
    @property
    def value(self) -> str:
        return self._value_


Keychain = NewType('Keychain', tuple[str, ...])

KT = TypeVar('KT')
VT = TypeVar('VT')


class FinalDict(dict[KT, VT]):
    """dictionary which raises KeyError if trying to overwrite existing value."""

    def __setitem__(self, k: KT, v: VT) -> None:
        if cv := self.get(k):
            raise NotionDfKeyError('cannot overwrite FinalDict',
                                   {'key': k, 'new_value': v, 'current_value': cv})
        super().__setitem__(k, v)


class FinalClassDict(dict[KT, VT]):
    """dictionary which raises KeyError if trying to overwrite existing value.
    however if the new value is subclass of current value, error would not be raised.
    this is useful when you try to register a static class attributes as a mapping."""

    def __setitem__(self, k: KT, v: VT) -> None:
        if cv := self.get(k):
            if issubclass(v, cv):
                return
            raise NotionDfKeyError('cannot overwrite FinalDict',
                                   {'key': k, 'new_value': v, 'current_value': cv})
        super().__setitem__(k, v)


class DictFilter:
    @staticmethod
    def truthy(d: dict[KT, VT]) -> dict[KT, VT]:
        return {k: v for k, v in d.items() if v}

    @staticmethod
    def not_none(d: dict[KT, VT]) -> dict[KT, VT]:
        return {k: v for k, v in d.items() if v is not None}


T = TypeVar('T')


class Paginator(Sequence[T]):
    def __init__(self, element_type: type[T], it: Iterator[T]):
        self.element_type: type[T] = element_type
        """used on repr()"""
        self._it: Iterator[T] = it
        self._values: list[T] = []

    def __repr__(self):
        return repr_object(self, ['element_type'])

    def _fetch_until(self, index: int) -> None:
        """fetch until self._values[index] is possible"""
        while len(self._values) <= index:
            try:
                self._values.append(next(self._it))
            except StopIteration:
                raise NotionDfIndexError("Index out of range", {'self': self, 'index': index})

    def _fetch_all(self) -> None:
        for element in self._it:
            self._values.append(element)

    @overload
    def __getitem__(self, index_or_id: int) -> T:
        ...

    @overload
    def __getitem__(self, index_or_id: slice) -> list[T]:
        ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        if isinstance(index, int):
            if index >= 0:
                self._fetch_until(index)
            else:
                self._fetch_all()
            return self._values[index]
        if isinstance(index, slice):
            step = index.step if index.step is not None else 1

            if ((index.start is not None and index.start < 0)
                    or (index.stop is not None and index.stop < 0)
                    or (index.stop is None and step > 0)
                    or (index.start is None and step < 0)):
                self._fetch_all()
                return self._values[index]

            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else 0
            self._fetch_until(max(start, stop))
            return [self._values[i] for i in range(start, stop, step)]
        else:
            raise NotionDfTypeError("bad argument - expected int or slice", {'self': self, 'index': index})

    def __len__(self):
        self._fetch_all()
        return len(self._values)

    @classmethod
    def chain(cls, element_type: type[T], paginator_it: Iterable[Paginator[T]]) -> Paginator[T]:
        return Paginator(element_type, chain.from_iterable(paginator_it))

    @classmethod
    def empty(cls, element_type: type[T]) -> Paginator[T]:
        return Paginator(element_type, iter([]))

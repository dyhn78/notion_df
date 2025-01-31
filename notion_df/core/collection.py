from __future__ import annotations

from dataclasses import fields
from enum import Enum
from itertools import chain
from typing import TypeVar, NewType, Iterable, Optional, Iterator, Sequence, overload

from notion_df.core.exception import ImplementationError
from notion_df.core.struct import repr_object


class StrEnum(str, Enum):  # TODO: use builtin StrEnum after py3.11
    @property
    def value(self) -> str:
        return self._value_


class PlainStrEnum(StrEnum):
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


Keychain = NewType("Keychain", tuple[str, ...])

KT = TypeVar("KT")
VT = TypeVar("VT")


class FinalDict(dict[KT, VT]):
    """dictionary which raises KeyError if trying to overwrite existing value."""

    def __setitem__(self, k: KT, v: VT) -> None:
        if cv := self.get(k):
            raise ImplementationError(
                "cannot overwrite FinalDict",
                {"key": k, "new_value": v, "current_value": cv},
            )
        super().__setitem__(k, v)


class DictFilter:
    @staticmethod
    def truthy(d: dict[KT, VT]) -> dict[KT, VT]:
        return {k: v for k, v in d.items() if v}

    @staticmethod
    def not_none(d: dict[KT, VT]) -> dict[KT, VT]:
        return {k: v for k, v in d.items() if v is not None}


T = TypeVar("T")


def peek(it: Iterable[T]) -> Optional[Iterator[T]]:
    it = iter(it)
    try:
        _first_element = next(it)
    except StopIteration:
        return None
    return chain([_first_element], it)


class Paginator(Sequence[T]):
    def __init__(self, element_type: type[T], it: Iterator[T]):
        self.element_type: type[T] = element_type
        """used on repr()"""
        self._it: Iterator[T] = it
        self._values: list[T] = []

    def __repr__(self):
        return repr_object(self, element_type=self.element_type)

    def _fetch_until(self, index: int) -> None:
        """fetch until self._values[index] is possible"""
        while len(self._values) <= index:
            try:
                self._values.append(next(self._it))
            except StopIteration:
                return

    def _fetch_all(self) -> None:
        for element in self._it:
            self._values.append(element)

    def __len__(self):
        self._fetch_all()
        return len(self._values)

    @overload
    def __getitem__(self, index_or_id: int) -> T: ...

    @overload
    def __getitem__(self, index_or_id: slice) -> list[T]: ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        if isinstance(index, int):
            if index >= 0:
                self._fetch_until(index)
            else:
                self._fetch_all()
            return self._values[index]
        if isinstance(index, slice):
            step = index.step if index.step is not None else 1

            if (
                (index.start is not None and index.start < 0)
                or (index.stop is not None and index.stop < 0)
                or (index.stop is None and step > 0)
                or (index.start is None and step < 0)
            ):
                self._fetch_all()
                return self._values[index]

            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else 0
            self._fetch_until(max(start, stop))
            return self._values[start:stop:step]
        else:
            raise TypeError(f"Expected int or slice, {self=}, {index=}")


def coalesce_dataclass(target: T, source: T) -> None:
    """Modify the target, by filling None fields from source."""
    if type(target) is not type(source):
        raise ValueError("Both instances must be of the same dataclass type.")
    for field in fields(target):
        if getattr(target, field.name) is None:
            setattr(target, field.name, getattr(source, field.name))

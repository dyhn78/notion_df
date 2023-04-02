from __future__ import annotations

from enum import Enum
from typing import Mapping, TypeVar, Iterator, Final, Any

from notion_df.util.misc import repr_object, NotionDfKeyError
from notion_df.util.mixin import Resolvable

_T_co = TypeVar('_T_co', covariant=True)
_VT_co = TypeVar('_VT_co', covariant=True)


class DictView(Mapping[_T_co, _VT_co]):
    """immutable, synchronized view of dictionary."""

    def __init__(self, _data_input: dict[_T_co, _VT_co] | Resolvable[dict[_T_co, _VT_co]], **description: str):
        self._data_input = _data_input
        self._is_promise = hasattr(_data_input, 'resolve')
        self.description: Final = description

    @property
    def _model(self) -> dict[_T_co, _VT_co]:
        if self._is_promise:
            return self._data_input.resolve()
        return self._data_input

    def __getitem__(self, key: _T_co) -> _VT_co:
        return self._model.__getitem__(key)

    def __len__(self) -> int:
        return self._model.__len__()

    def __iter__(self) -> Iterator[_T_co]:
        return self._model.__iter__()

    def __repr__(self) -> str:
        return repr_object(self, **self.description, data=self._model)


class StrEnum(str, Enum):
    @property
    def value(self) -> str:
        return self._value_


class KeyChain(tuple[str, ...]):
    def __add__(self, other: tuple[str, ...]) -> KeyChain:
        return KeyChain(tuple(self) + other)

    def get(self, d: dict) -> Any:
        for key in self:
            d = d[key]
        return d

    def set(self, d: dict, value: Any) -> None:
        if not self:
            return
        for key in self[:-1]:
            d = d[key]
        d[self[-1]] = value


_KT = TypeVar('_KT')
_VT = TypeVar('_VT')


class FinalDict(dict[_KT, _VT]):
    """dictionary which raises KeyError if trying to overwrite existing value."""

    def __setitem__(self, k: _KT, v: _VT) -> None:
        if cv := self.get(k):
            raise NotionDfKeyError('cannot overwrite FinalDict',
                                   {'key': k, 'new_value': v, 'current_value': cv})
        super().__setitem__(k, v)


class FinalClassDict(dict[_KT, _VT]):
    """dictionary which raises KeyError if trying to overwrite existing value.
    however if the new value is subclass of current value, error would not be raised.
    this is useful when you try to register a static class attributes as a mapping."""

    def __setitem__(self, k: _KT, v: _VT) -> None:
        if cv := self.get(k):
            if issubclass(v, cv):
                return
            raise NotionDfKeyError('cannot overwrite FinalDict',
                                   {'key': k, 'new_value': v, 'current_value': cv})
        super().__setitem__(k, v)


def filter_truthy(d: dict[_KT, _VT]) -> dict[_KT, _VT]:
    return {k: v for k, v in d.items() if v}


def filter_out_none(d: dict[_KT, _VT]) -> dict[_KT, _VT]:
    return {k: v for k, v in d.items() if v is not None}

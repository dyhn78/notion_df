from __future__ import annotations

from enum import Enum
from typing import Mapping, TypeVar, Iterator, Final, NewType

from notion_df.util.exception import NotionDfKeyError
from notion_df.util.misc import repr_object

_T_co = TypeVar('_T_co', covariant=True)
_VT_co = TypeVar('_VT_co', covariant=True)


class Resolvable(Generic[_T]):
    @abstractmethod
    def resolve(self) -> _T:
        pass


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
        return repr_object(self, {'data': self._model, **self.description})

from enum import Enum
from typing import Mapping, TypeVar, Iterator, Final

from notion_df.util import repr_object
from notion_df.util.mixin import Promise

_T_co = TypeVar('_T_co', covariant=True)
_VT_co = TypeVar('_VT_co', covariant=True)


class DictView(Mapping[_T_co, _VT_co]):
    """immutable, synchronized view of dictionary."""

    def __init__(self, _data_input: dict[_T_co, _VT_co] | Promise[dict[_T_co, _VT_co]], **description: str):
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


class StrEnum(Enum):
    @property
    def value(self) -> str:
        return self._value_

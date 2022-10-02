from typing import Mapping, TypeVar, Iterator, Final

from notion_df.utils import repr_object

_T_co = TypeVar('_T_co', covariant=True)
_VT_co = TypeVar('_VT_co', covariant=True)


class DictView(Mapping[_T_co, _VT_co]):
    """immutable, synchronized view of dictionary."""

    def __init__(self, data: dict[_T_co, _VT_co], **description: str):
        self._data = data
        self.description: Final = description

    def __getitem__(self, key: _T_co) -> _VT_co:
        return self._data.__getitem__(key)

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> Iterator[_T_co]:
        return self._data.__iter__()

    def __repr__(self) -> str:
        return repr_object(self, **self.description, data=self._data)

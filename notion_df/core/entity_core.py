from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Final, Generic, Hashable, Union, Optional, final
from uuid import UUID

from typing_extensions import Self

from notion_df.core.request import Data_T
from notion_df.util.misc import repr_object, undefined

namespace: Final[dict[tuple[type[Entity], UUID], Entity]] = {}  # TODO: support multiple entities


class Entity(Generic[Data_T], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.
    There is only one instance with given subclass and id.
    You can compare two blocks directly `block_1 == block_2`, not having to compare id `block_1.id == block_2.id`"""
    id: UUID
    _data: Optional[Data_T] = None
    """the latest data of the entity, which does not trigger auto-retrieve. None if empty."""

    @classmethod
    @abstractmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        pass

    def __new__(cls, id_or_url: Union[UUID, str]):
        try:
            __id = cls._get_id(id_or_url)
            if (cls, __id) in namespace:
                return namespace[(cls, __id)]
            return super().__new__(cls)
        finally:
            del __id

    def __init__(self, id_or_url: Union[UUID, str]):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.id: Final[UUID] = self._get_id(id_or_url)
        namespace[(type(self), self.id)] = self
        self._data: Optional[Data_T] = None

    def __del__(self):
        del self.data
        del namespace[(type(self), self.id)]

    def __getnewargs__(self):  # required for pickling
        return self.id,

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def __eq__(self, other: Entity) -> bool:
        return type(self) == type(other) and self.id == other.id

    def __repr__(self) -> str:
        return repr_object(self, id=self.id, parent=self._repr_parent())

    @final
    def _repr_parent(self) -> Optional[str]:
        if self._data is None:
            return undefined
        elif self._data.parent is None:
            return 'workspace'
        else:  # TODO: fix that user and comments does not have parent
            return self._data.parent._repr_as_parent()

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)

    @property
    def data(self) -> Data_T:
        """the latest data of the entity. if there is no local data yet, automatically retrieve it."""
        if self._data is None:
            self.retrieve()  # TODO: raise EntityNotExistError(ValueError), with validate_page_existence()
        return self._data

    @data.setter
    def data(self, data: Data_T) -> None:
        """keep the latest data between the current data and new data."""
        if data.timestamp > (self._data.timestamp if self._data else 0):
            self._send_data(data)
            self._data = data

    @data.deleter
    def data(self) -> None:
        """reset the data, so that you can force-retrieve next time or intentionally pass the outdated data."""
        self._data = None

    def _send_data(self, data: Data_T) -> None:
        """copy the "proper attributes" to entity (without `data` and `last_timestamp`)"""
        pass  # TODO delete

    @abstractmethod
    def retrieve(self) -> Self:
        pass

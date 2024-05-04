from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Final, Generic, Hashable, Union, Optional, final
from uuid import UUID

from typing_extensions import Self

from notion_df.core.data import DataT
from notion_df.util.misc import repr_object, undefined

namespace: Final[dict[tuple[type[Entity], UUID], Entity]] = {}


class Entity(Generic[DataT], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.
    There is only one instance with given subclass and id.
    You can compare two blocks directly `block_1 == block_2`, not having to compare id `block_1.id == block_2.id`"""
    id: UUID
    data: Optional[DataT] = None
    """the latest local data of the entity."""

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

    def __del__(self):
        # TODO: use weakref instead. validate it with unit test which assert sys.getrefcount()
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
        if self.data is None:
            return undefined
        elif self.data.parent is None:
            return 'workspace'
        else:  # TODO: fix that user and comments does not have parent
            return self.data.parent._repr_as_parent()

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)

    def get_data(self) -> DataT:
        """get the local data, or retrieve if there is not."""
        if self.data is None or not self.data.timestamp:
            self.retrieve()  # TODO: raise EntityNotExistError(ValueError), with page_exists()
        return self.data

    def set_data(self, data: DataT) -> Self:
        """set the data as the more recent one between current one and new one."""
        if (self.data is None) or (data.timestamp > self.data.timestamp):
            self.data = data
        return self

    @abstractmethod
    def retrieve(self) -> Self:
        pass

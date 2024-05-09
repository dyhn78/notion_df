from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import (Final, Generic, Hashable, Union, Optional, final, TypeVar, Any, cast as typing_cast)
from uuid import UUID

from typing_extensions import Self

from notion_df.core.data import DataT, EntityData, coalesce
from notion_df.util.misc import repr_object, undefined

namespace: Final[dict[tuple[type[Entity], UUID], Entity]] = {}
DataT2 = TypeVar("DataT2", bound=EntityData)


class Entity(Generic[DataT], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.

    There is only one instance with given subclass and id.
    You can identify two blocks directly `block_1 == block_2`,
    not need to `block_1.id == block_2.id`

    Use `default` attribute to hardcode some data (which can reduce API calls)
    """
    id: UUID
    __latest: Optional[DataT] = None
    default: Optional[DataT] = None
    """custom local-only data."""

    @classmethod
    @abstractmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        pass

    def __new__(cls, id_or_url: Union[UUID, str],
                default: Optional[DataT] = None,
                *, latest: Optional[EntityData] = None):
        try:
            __id = cls._get_id(id_or_url)
            if (cls, __id) in namespace:
                return namespace[(cls, __id)]
            return super().__new__(cls)
        finally:
            del __id

    def __init__(self, id_or_url: Union[UUID, str],
                 default: Optional[DataT] = None,
                 *, latest: Optional[EntityData] = None):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.id: Final[UUID] = self._get_id(id_or_url)
            namespace[(type(self), self.id)] = self
        self.latest = latest
        self.default = default

    def __del__(self):
        # TODO: consider using weakref instead.
        #  validate it with unit test which assert sys.getrefcount()
        del self.latest
        del namespace[(type(self), self.id)]

    def __getnewargs__(self):  # required for pickling
        return self.id,

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Entity)
                and ((type(self), self.id) == (type(other), self.id)))

    def __repr__(self) -> str:
        return repr_object(self, id=self.id, parent=self._repr_parent())

    @property
    def latest(self) -> Optional[DataT]:
        """the latest data from the server."""
        return self.__latest

    @latest.setter
    def latest(self, contents: DataT) -> None:
        """set the data as the more recent one between current one and new one."""
        if (self.latest is None) or (contents.timestamp > self.latest.timestamp):
            self.__latest = contents

    @latest.deleter
    def latest(self) -> None:
        self.__latest = None

    @property
    def data(self) -> Optional[DataT]:
        """get the local data."""
        return coalesce(self.latest, self.default)

    @final
    def _repr_parent(self) -> Optional[str]:
        contents = self.data  # prevents retrieve_if_empty
        if contents is None or not hasattr(contents, 'parent'):
            return undefined
        elif contents.parent is None:
            return 'workspace'
        else:  # TODO: fix that user and comments does not have parent
            return typing_cast(Entity, contents.parent)._repr_as_parent()

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)


class RetrievableEntity(Entity[DataT]):
    @abstractmethod
    def retrieve(self) -> Self:
        # TODO: raise EntityNotExistError(ValueError), with page_exists()
        pass

    @property
    def data(self) -> DataT:
        """get the local data, or auto-retrieve."""
        contents = coalesce(self.latest, self.default)
        if contents is not None:
            return contents
        self.retrieve()
        return typing_cast(DataT, self.latest)

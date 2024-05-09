from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import (Final, Generic, Hashable, Union, Optional, final, TypeVar, Any, cast)
from uuid import UUID

from typing_extensions import Self

from notion_df.core.data import EntityDataT, EntityData, latest_data_dict
from notion_df.util.misc import repr_object, undefined

EntityDataT2 = TypeVar("EntityDataT2", bound=EntityData)


class Entity(Generic[EntityDataT], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.

    There is only one instance with given subclass and id.
    You can identify two blocks directly `block_1 == block_2`,
    not need to `block_1.id == block_2.id`

    Use `default` attribute to hardcode some data (which can reduce API calls)
    """
    id: UUID
    __latest: Optional[EntityDataT] = None
    _DataT: type[EntityDataT]

    def __init_subclass__(cls, **kwargs):
        assert cls._DataT

    @classmethod
    @abstractmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        pass

    def __init__(self, id_or_url: Union[UUID, str]):
        self.id: Final[UUID] = self._get_id(id_or_url)

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
    def data(self) -> Optional[EntityDataT]:
        """this always points at the latest data of the entity."""
        return latest_data_dict.get((self._DataT, self.id))

    @data.deleter
    def data(self) -> None:
        del self.data

    @final
    def _repr_parent(self) -> Optional[str]:
        contents = self.data  # prevents retrieve_if_empty
        if contents is None or not hasattr(contents, 'parent'):
            return undefined
        elif contents.parent is None:
            return 'workspace'
        else:  # TODO: fix that user and comments does not have parent
            return cast(Entity, contents.parent)._repr_as_parent()

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)


class RetrievableEntity(Entity[EntityDataT]):
    @abstractmethod
    def retrieve(self) -> Self:
        # TODO: raise EntityNotExistError(ValueError), with page_exists()
        pass

    @property
    def latest(self) -> EntityDataT:
        """get the local data, or auto-retrieve."""
        if data := super().data:
            return data
        self.retrieve()
        return cast(EntityDataT, super().data)

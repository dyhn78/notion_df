from __future__ import annotations

from abc import abstractmethod, ABCMeta
from functools import cache
from inspect import isabstract
from typing import (
    Final,
    Generic,
    Hashable,
    Union,
    final,
    TypeVar,
    Any,
    Callable,
    ClassVar,
)
from uuid import UUID

from loguru import logger
from typing_extensions import Self

from notion_df.core.data_core import EntityDataT, real_data_dict, preview_data_dict
from notion_df.core.exception import ImplementationError
from notion_df.core.struct import undefined, repr_object, Undefined


class Entity(Hashable, Generic[EntityDataT], metaclass=ABCMeta):
    """The base class for blocks, users, and comments.

    Two entities will be equal if their class and id are the same.
    """

    id: UUID

    @classmethod
    @abstractmethod
    def _get_data_cls(cls) -> type[EntityDataT]:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @staticmethod
    @abstractmethod
    def _get_id(id_or_url: Union[UUID, str]) -> UUID:
        pass

    def __init__(self, id_or_url: UUID | str):
        self.id: Final[UUID] = self._get_id(id_or_url)

    def __getnewargs__(self):  # required for pickling
        return (self.id,)

    @property
    def _hash_key(self) -> tuple[type[EntityDataT], UUID]:
        return self._get_data_cls(), self.id

    def __hash__(self) -> int:
        return hash(self._hash_key)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Entity) and self._hash_key == other._hash_key

    def __repr__(self) -> str:
        return repr_object(self, id=self.id)

    @property
    def data(self) -> Union[EntityDataT, Undefined]:
        """
        - If there is any local data, return it. (You should call `retrieve()` if you really want the up-to-date data.)
        - If there is no local data, and its class is retrievable, retrieve it. (Use `local_data` if you want to avoid this.)
        - If there is no local data, and its class is not retrievable, return undefined.
        """
        return self.local_data

    @final
    @property
    def local_data(self) -> Union[EntityDataT, Undefined]:
        """Use this instead of `data` if you want to avoid on-demand retrieval."""
        return real_data_dict.get(
            self._hash_key, preview_data_dict.get(self._hash_key, undefined)
        )


CallableT = TypeVar("CallableT", bound=Callable)


def retrieve_on_demand(func: CallableT) -> CallableT:
    def wrapper(self: RetrievableEntity, *args, **kwargs):
        if (result := func(self, *args, **kwargs)) is not undefined:
            return result
        logger.debug(f"retrieve on-demand, {self=}")
        self.retrieve()
        if (result := func(self, *args, **kwargs)) is not undefined:
            return result
        raise ImplementationError(f"{type(self)}.retrieve() did not update latest data")

    return wrapper


class RetrievableEntity(Entity[EntityDataT]):
    @abstractmethod
    def retrieve(self) -> Self:
        # TODO: raise EntityNotExistError(ValueError), with page_exists()
        pass

    @final
    @property
    @retrieve_on_demand
    def data(self) -> EntityDataT:
        return self.local_data


# TODO: Generic[ChildrenT]
class HaveChildren(metaclass=ABCMeta):
    @abstractmethod
    def _repr_as_parent(self) -> str:
        pass


class HaveParentAndChildren(Entity, HaveChildren, metaclass=ABCMeta):
    @property
    @abstractmethod
    def parent(self) -> HaveChildren:
        pass

    @final
    def _repr_parent(self) -> str:
        if not self.local_data:
            return undefined
        return self.parent._repr_as_parent()

    def __repr__(self) -> str:
        return repr_object(self, id=self.id, parent=self._repr_parent())


class BaseBlock(RetrievableEntity[EntityDataT], HaveParentAndChildren, metaclass=ABCMeta):
    """base class for Block, Database, Page"""
    pass

from __future__ import annotations

from abc import abstractmethod, ABCMeta
from inspect import isabstract
from typing import (Final, Generic, Hashable, Union, Optional, final, TypeVar, Any, cast, MutableMapping, Callable)
from uuid import UUID
from weakref import WeakValueDictionary

from typing_extensions import Self

from notion_df.core.data import EntityDataT, EntityData
from notion_df.util.misc import repr_object, undefined

latest_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = WeakValueDictionary()
default_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = {}


class Entity(Generic[EntityDataT], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.

    There is only one instance with given subclass and id.
    You can identify two blocks directly `block_1 == block_2`,
    not need to `block_1.id == block_2.id`

    Use `default` attribute to hardcode some data (which can reduce API calls)
    """
    id: UUID
    data_cls: type[EntityDataT]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not isabstract(cls):
            assert cls.data_cls

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
        return self.local_data

    @final
    @property
    def local_data(self) -> Optional[EntityDataT]:
        key = (self.data_cls, self.id)
        return latest_data_dict.get(key, default_data_dict.get(key))

    def set_data(self, data: EntityDataT) -> Self:
        current_latest_data = latest_data_dict.get((self.data_cls, self.id))
        if current_latest_data is None or data.timestamp >= current_latest_data.timestamp:
            latest_data_dict[self.data_cls, self.id] = data
        return self

    @abstractmethod
    def set_default_data(self, **kwargs: Any) -> Self:
        """default data is always at the last priority of reading data and not garbage collected.
        use it to hardcode invariant values (such as the root pages of your workspace)."""
        pass

    def _set_default_data(self, data: EntityDataT) -> Self:
        default_data_dict[self.data_cls, self.id] = data
        return self

    # TODO: create HasParent, CanBeParent base class
    @final
    def _repr_parent(self) -> Optional[str]:
        if not self.local_data or not hasattr(self.local_data, 'parent'):
            return undefined
        elif self.local_data.parent is None:
            return 'workspace'
        else:  # TODO: fix that user and comments does not have parent
            return cast(Entity, self.local_data.parent)._repr_as_parent()

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)


CallableT = TypeVar("CallableT", bound=Callable)


def retrieve_if_undefined(func: CallableT) -> CallableT:
    def wrapper(self: RetrievableEntity, *args, **kwargs):
        if (result := func(*args, **kwargs)) is not undefined:
            return result
        self.retrieve()
        if (result := func(*args, **kwargs)) is not undefined:
            return result
        raise RuntimeError(f"{type(self)}.retrieve() did not update latest data")

    return wrapper


class RetrievableEntity(Entity[EntityDataT]):
    @abstractmethod
    def retrieve(self) -> Self:
        # TODO: raise EntityNotExistError(ValueError), with page_exists()
        pass

    @property
    @retrieve_if_undefined
    def data(self) -> EntityDataT:
        return self.local_data

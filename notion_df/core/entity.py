from __future__ import annotations

from abc import abstractmethod, ABCMeta
from inspect import isabstract
from typing import (Final, Generic, Hashable, Union, Optional, final, TypeVar, Any, MutableMapping, Callable, ClassVar)
from uuid import UUID
from weakref import WeakValueDictionary

from typing_extensions import Self

from notion_df.core.data import EntityDataT, EntityData
from notion_df.util.misc import repr_object, undefined

_latest_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = WeakValueDictionary()
_default_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = {}


class Entity(Generic[EntityDataT], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.

    There is only one instance with given subclass and id.
    You can identify two blocks directly `block_1 == block_2`,
    not need to `block_1.id == block_2.id`
    """
    id: UUID
    # noinspection PyClassVar
    data_cls: ClassVar[type[EntityDataT]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not isabstract(cls):
            assert cls.data_cls

    @staticmethod
    @abstractmethod
    def _get_id(id_or_url: Union[UUID, str]) -> UUID:
        pass

    def __init__(self, id_or_url: Union[UUID, str]):
        self.id: Final[UUID] = self._get_id(id_or_url)

    def __getnewargs__(self):  # required for pickling
        return self.id,

    @property
    def _hash_key(self) -> tuple[type[EntityDataT], UUID]:
        return self.data_cls, self.id

    def __hash__(self) -> int:
        return hash(self._hash_key)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Entity) and self._hash_key == other._hash_key

    def __repr__(self) -> str:
        return repr_object(self, id=self.id)

    @property
    def data(self) -> Optional[EntityDataT]:
        """this always points at the latest data of the entity."""
        return self.local_data

    @final
    @property
    def local_data(self) -> Optional[EntityDataT]:
        return _latest_data_dict.get(self._hash_key, _default_data_dict.get(self._hash_key))

    def set_data(self, data: EntityDataT) -> Self:
        current_latest_data = _latest_data_dict.get(self._hash_key)
        if current_latest_data is None or data.timestamp >= current_latest_data.timestamp:
            _latest_data_dict[self._hash_key] = data
        return self

    @abstractmethod
    def set_default_data(self, **kwargs: Any) -> Self:
        """default data is always at the last priority of reading data and not garbage collected.
        use it to hardcode invariant values (such as the root pages of your workspace)."""
        pass

    def _set_default_data(self, data: EntityDataT) -> Self:
        _default_data_dict[self._hash_key] = data
        return self


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


CallableT = TypeVar("CallableT", bound=Callable[[RetrievableEntity, ...], Any])


class CanBeParent(metaclass=ABCMeta):
    @abstractmethod
    def _repr_as_parent(self) -> str:
        pass


class HasParent(Entity, CanBeParent, metaclass=ABCMeta):
    @property
    @abstractmethod
    def parent(self) -> CanBeParent:
        pass

    @final
    def _repr_parent(self) -> str:
        if not self.local_data:
            return undefined
        return self.parent._repr_as_parent()

    def __repr__(self) -> str:
        return repr_object(self, id=self.id, parent=self._repr_parent())

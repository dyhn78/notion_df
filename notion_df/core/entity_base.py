from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Final, Generic, Hashable, Union, Optional, final
from uuid import UUID

from typing_extensions import Self

from notion_df.core.request import Response_T
from notion_df.util.misc import repr_object, undefined

namespace: Final[dict[tuple[type[Entity], UUID], Entity]] = {}  # TODO: support multiple entities


class Entity(Generic[Response_T], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.
    There is only one instance with given subclass and id.
    You can compare two blocks directly `block_1 == block_2`, not having to compare id `block_1.id == block_2.id`"""
    id: UUID
    parent: Optional[Entity]  # TODO: fix that user and comments does not have parent
    last_response: Optional[Response_T]
    """the latest response received by `send_response()`. 
    this is initialized as None unlike the "proper attributes" (parent, title, properties)"""
    last_timestamp: float
    """timestamp of last response. initialized as 0."""

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
        self.last_response = None
        self.last_timestamp = 0

    def __del__(self):
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
        if not hasattr(self, 'parent'):
            return undefined
        elif self.parent is None:
            return 'workspace'
        else:
            return self.parent._repr_as_parent()

    def _repr_as_parent(self) -> Optional[str]:
        return repr_object(self, id=self.id)

    @final
    def send_response(self, response: Response_T) -> Self:
        if response.timestamp > self.last_timestamp:
            self._send_response(response)
            self.last_response = response
            self.last_timestamp = response.timestamp
        return self

    @abstractmethod
    def _send_response(self, response: Response_T) -> None:
        """copy the "proper attributes" to entity (without `last_response` and `last_timestamp`)"""
        pass

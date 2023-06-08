from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Final, Generic, Hashable, Union, Optional, final, Any
from uuid import UUID

from typing_extensions import Self

from notion_df.core.request import Response_T
from notion_df.util.misc import repr_object

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

    def __getnewargs__(self):
        return self.id,

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def __eq__(self, other: Entity) -> bool:
        return type(self) == type(other) and self.id == other.id

    @final
    def __repr__(self) -> str:
        if not hasattr(self, 'parent'):
            repr_parent = None
        elif self.parent is None:
            repr_parent = 'workspace'
        else:
            # TODO: fix `Entity(parent='Database()') <- remove this '' around parent value
            repr_parent = repr_object(self.parent, self.parent._attrs_to_repr_parent())

        return repr_object(self, {
            **self._attrs_to_repr_parent(),
            'id_or_url': getattr(self, 'url', str(self.id)),
            'parent': repr_parent
        })

    def _attrs_to_repr_parent(self) -> dict[str, Any]:
        return {}

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

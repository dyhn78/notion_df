from __future__ import annotations

import functools
from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar, Optional, NoReturn, final
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import Deserializable


@dataclass
class EntityData(Deserializable, metaclass=ABCMeta):
    id: UUID
    raw: dict[str, Any] = field(init=False, default_factory=dict)
    timestamp: int = field(init=False)
    """the timestamp of deserialization if created with external raw data, 
    or 0 if created by user."""

    def __post_init__(self) -> None:
        self.timestamp = int(datetime.now().timestamp())

    def __del__(self) -> None:
        del self.raw

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        _deserialize_this = cls._deserialize_this

        @functools.wraps(_deserialize_this)
        def _deserialize_this_wrapped(raw: dict[str, Any]) -> Self:
            self: EntityData = _deserialize_this(raw)
            self.raw = raw
            return self

        setattr(cls, '_deserialize_this', _deserialize_this_wrapped)

    @classmethod
    def deserialize(cls, raw: Any) -> Self:
        from notion_df.object.data import BlockData, DatabaseData, PageData

        if cls != EntityData:
            return cls._deserialize_this(raw)
        match object_kind := raw['object']:
            case 'block':
                subclass = BlockData
            case 'database':
                subclass = DatabaseData
            case 'page':
                subclass = PageData
            case _:
                raise ValueError(object_kind)
        return subclass.deserialize(raw)

    @property
    def time(self) -> Optional[datetime]:
        """the time of deserialization if created with external raw data,
         or None if created by user."""
        return datetime.fromtimestamp(self.timestamp) if self.timestamp else None

    @final
    def cast(self, cls: type[EntityDataT]) -> EntityDataT:
        return cls.cast_from(self)

    @classmethod
    def cast_from(cls, instance: EntityData) -> Self:
        # the default classes (ex. BlockData) should NOT override this
        # TODO: force that custom subclasses to override this
        return instance

    def __getitem__(self) -> NoReturn:
        # TODO: call properties.__getitem__
        raise NotImplementedError


EntityDataT = TypeVar('EntityDataT', bound=EntityData)

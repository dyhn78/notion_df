from __future__ import annotations

import functools
from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar, Optional

from typing_extensions import Self

from notion_df.core.serialization import Deserializable


@dataclass
class Data(Deserializable, metaclass=ABCMeta):
    raw: dict[str, Any] = field(init=False, default_factory=dict)
    timestamp: int = field(init=False, default=0)
    """the timestamp of deserialization if created with external raw data, or 0 if created by user."""

    def __del__(self):
        del self.raw

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        _deserialize_this = cls._deserialize_this

        @functools.wraps(_deserialize_this)
        def _deserialize_this_wrapped(raw: dict[str, Any]) -> Self:
            self: Data = _deserialize_this(raw)
            self.raw = raw
            self.timestamp = datetime.now().timestamp()
            return self

        setattr(cls, '_deserialize_this', _deserialize_this_wrapped)

    @classmethod
    def deserialize(cls, raw: Any) -> Self:
        from notion_df.object.data import BlockData, DatabaseData, PageData

        if cls != Data:
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
        """the time of deserialization if created with external raw data, or None if created by user."""
        return datetime.fromtimestamp(self.timestamp) if self.timestamp else None


Data_T = TypeVar('Data_T', bound=Data)

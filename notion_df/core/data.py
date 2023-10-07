from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar
from typing_extensions import Self

from notion_df.core.serialization import Deserializable


@dataclass
class Data(Deserializable, metaclass=ABCMeta):
    timestamp: float = field(init=True, kw_only=True, default_factory=datetime.now().timestamp)
    raw: dict[str, Any] = field(init=False, default=None)

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw, raw=raw)

    @classmethod
    def deserialize(cls, serialized: Any) -> Self:
        from notion_df.object.data import BlockData, DatabaseData, PageData

        if cls != Data:
            return cls._deserialize_this(serialized)

        match object_kind := serialized['object']:
            case 'block':
                subclass = BlockData
            case 'database':
                subclass = DatabaseData
            case 'page':
                subclass = PageData
            case _:
                raise ValueError(object_kind)
        return subclass.deserialize(serialized)

    def __del__(self):
        del self.raw


Data_T = TypeVar('Data_T', bound=Data)

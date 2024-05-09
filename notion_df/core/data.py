from __future__ import annotations

import functools
from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar, MutableMapping, Final
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import Deserializable

latest_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = {}
hardcoded_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = {}


@dataclass
class EntityData(Deserializable, metaclass=ABCMeta):
    id: UUID
    raw: dict[str, Any] = field(init=False, default_factory=dict)
    timestamp: int = field(init=False)
    """the timestamp of deserialization if created with external raw data, 
    or 0 if created by user."""
    hardcoded: bool = field(kw_only=True, default=False)

    def __post_init__(self) -> None:
        self.timestamp = int(datetime.now().timestamp())
        hash_key = type(self), self.id
        if self.hardcoded:
            # TODO: merge with current hardcoded data
            hardcoded_data_dict[hash_key] = self
        else:
            current_latest_data = latest_data_dict.get(hash_key)
            if current_latest_data is None or self.timestamp >= current_latest_data.timestamp:
                latest_data_dict[hash_key] = self

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
    def time(self) -> datetime:
        """the created time of the instance."""
        return datetime.fromtimestamp(self.timestamp)


EntityDataT = TypeVar('EntityDataT', bound=EntityData)

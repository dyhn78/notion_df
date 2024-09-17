from __future__ import annotations

import functools
from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar, MutableMapping, Final
from uuid import UUID

from loguru import logger
from typing_extensions import Self

from notion_df.core.collection import coalesce_dataclass
from notion_df.core.serialization import Deserializable


@dataclass
class EntityData(Deserializable, metaclass=ABCMeta):
    id: UUID
    raw: dict[str, Any] = field(init=False, default_factory=dict)
    timestamp: int = field(init=False, default_factory=lambda: int(datetime.now().timestamp()))
    """the timestamp of instance creation."""
    mock: bool = field(kw_only=True, default=False)
    _finalized: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        logger.trace(self)
        self._finalized = True

    def __setattr__(self, key: str, value: Any) -> None:
        # TODO: use frozen=True
        if self._finalized and key != "_finalized":
            raise AttributeError(key, value)
        super().__setattr__(key, value)

    def __del__(self) -> None:
        del self.raw

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        _deserialize_this = cls._deserialize_this

        @functools.wraps(_deserialize_this)
        def _deserialize_this_wrapped(raw: dict[str, Any]) -> Self:
            self: EntityData = _deserialize_this(raw)
            self._finalized = False
            self.raw = raw
            self._finalized = True
            return self

        setattr(cls, '_deserialize_this', _deserialize_this_wrapped)

    @classmethod
    def _deserialize_subclass(cls, raw: Any) -> Self:
        from notion_df.data import BlockData, DatabaseData, PageData
        object_kind = raw['object']
        match object_kind:
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

from __future__ import annotations

# TODO: merge this file with ../data.py
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

real_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = {}
preview_data_dict: Final[MutableMapping[tuple[type[EntityData], UUID], EntityData]] = {}


@dataclass
class EntityData(Deserializable, metaclass=ABCMeta):
    id: UUID
    raw: dict[str, Any] = field(init=False, default_factory=dict)
    timestamp: int = field(
        init=False, default_factory=lambda: int(datetime.now().timestamp())
    )
    """the timestamp of instance creation."""
    finalized: bool = field(init=False, default=False)  # TODO use frozen=True

    def __post_init__(self) -> None:
        logger.trace(self)
        self.finalized = True

    def __setattr__(self, key: str, value: Any) -> None:
        # TODO: use frozen=True
        if getattr(self, "finalized", None) and key != "finalized":
            raise AttributeError(key, value)
        super().__setattr__(key, value)

    @property
    def _pk(self) -> tuple[type[EntityData], UUID]:
        return type(self), self.id

    def set_real(self) -> Self:
        """ATTEMPT to set the instance as the real data, if it is the latest."""
        current_latest_data = real_data_dict.get(self._pk)
        if (
            current_latest_data is None
            or self.timestamp >= current_latest_data.timestamp
        ):
            real_data_dict[self._pk] = self
        return self

    def unset_real(self) -> Self:
        """ATTEMPT to unset the instance from the real data, if it is the latest."""
        if real_data_dict.get(self._pk) is self:
            del real_data_dict[self._pk]
        return self

    def add_preview(self) -> Self:
        """set the instance as the preview data.
        if another preview data exists, coalesce them (this one has priority)."""
        if past_self := preview_data_dict.get(self._pk):
            self.finalized = False
            coalesce_dataclass(self, past_self)
            self.finalized = True
        preview_data_dict[self._pk] = self
        return self

    def clear_preview(self) -> Self:
        """unset the preview data."""
        del preview_data_dict[self._pk]
        return self

    def __del__(self) -> None:
        del self.raw

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        _deserialize_this = cls._deserialize_this

        @functools.wraps(_deserialize_this)
        def _deserialize_this_wrapped(raw: dict[str, Any]) -> Self:
            self: EntityData = _deserialize_this(raw)
            self.finalized = False
            self.raw = raw
            self.finalized = True
            return self

        setattr(cls, "_deserialize_this", _deserialize_this_wrapped)

    @classmethod
    def _deserialize_subclass(cls, raw: Any) -> Self:
        from notion_df.data import BlockData, DatabaseData, PageData

        object_kind = raw["object"]
        match object_kind:
            case "block":
                subclass = BlockData
            case "database":
                subclass = DatabaseData
            case "page":
                subclass = PageData
            case _:
                raise ValueError(object_kind)
        return subclass.deserialize(raw)

    @property
    def time(self) -> datetime:
        """the created time of the instance."""
        return datetime.fromtimestamp(self.timestamp)


EntityDataT = TypeVar("EntityDataT", bound=EntityData)

from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from typing_extensions import Self

from notion_df.core.exception import NotionDfValueError
from notion_df.core.serialization import serialize, deserialize, DualSerializable
from notion_df.data.common import Icon


@dataclass
class File(Icon, metaclass=ABCMeta):
    """https://developers.notion.com/reference/file-object"""

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != File:
            return cls._deserialize_this(serialized)
        match serialized['type']:
            case 'file':
                subclass = InternalFile
            case 'external':
                subclass = ExternalFile
            case _:
                raise NotionDfValueError('invalid relation_type',
                                         {'type': serialized['type'], 'serialized': serialized})
        return subclass.deserialize(serialized)


class Files(list[File], DualSerializable):
    def __init__(self, files: list[File]):
        super().__init__(files)

    @classmethod
    def externals(cls, url_name_pairs: list[tuple[str, str]]):
        return cls([ExternalFile(url, name) for url, name in url_name_pairs])

    def serialize(self) -> Any:
        return serialize(list(self))

    @classmethod
    def _deserialize_this(cls, serialized: Any) -> Self:
        return cls(deserialize(list[File], serialized))


@dataclass
class InternalFile(File):
    url: str
    expiry_time: datetime

    @classmethod
    def get_typename(cls) -> str:
        return 'file'

    def serialize(self):
        return {
            "type": "file",
            "file": {
                "url": self.url,
                "expiry_time": serialize(self.expiry_time)
            }
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['file']['url'], serialized['file']['expiry_time'])


@dataclass
class ExternalFile(File):
    url: str
    name: str

    @classmethod
    def get_typename(cls) -> str:
        return 'external'

    def serialize(self):
        return {
            "type": "external",
            "name": self.name,
            "external": {
                "url": self.url
            }
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['external']['url'], '')

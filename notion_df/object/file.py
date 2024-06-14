from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from typing_extensions import Self

from notion_df.core.exception import ImplementationError
from notion_df.core.serialization import serialize, deserialize, DualSerializable
from notion_df.object.misc import Icon


@dataclass
class File(Icon, metaclass=ABCMeta):
    """https://developers.notion.com/reference/file-object"""

    @classmethod
    def _deserialize_subclass(cls, raw: dict[str, Any]) -> Self:
        match raw['type']:
            case 'file':
                subclass = InternalFile
            case 'external':
                subclass = ExternalFile
            case _:
                raise ImplementationError(f"invalid relation_type, {raw['type']=}, {raw=}")
        return subclass.deserialize(raw)


class Files(list[File], DualSerializable):
    def __init__(self, files: list[File]):
        super().__init__(files)

    @classmethod
    def externals(cls, url_name_pairs: list[tuple[str, str]]):
        return cls([ExternalFile(url, name) for url, name in url_name_pairs])

    def serialize(self) -> Any:
        return serialize(list(self))

    @classmethod
    def _deserialize_this(cls, raw: Any) -> Self:
        return cls(deserialize(list[File], raw))


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
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw['file']['url'], raw['file']['expiry_time'])


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
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw['external']['url'], '')

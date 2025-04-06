from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self

from _scratch.serialization import TypenameDispatcher, Concrete
from notion_df.core.serialization import serialize_datetime


class Icon:
    dispatcher = TypenameDispatcher("Icon")


Icon.dispatcher = Icon.dispatcher


@Icon.dispatcher.register("emoji")
@dataclass
class Emoji(Concrete):
    """https://developers.notion.com/reference/emoji-object"""
    value: str

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value})"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def get_typename(cls) -> str:
        return "emoji"

    def serialize(self):
        return {"type": "emoji", "emoji": self.value}

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        return cls(data["emoji"])


File = TypenameDispatcher("File")
"""https://developers.notion.com/reference/file-object"""


@Icon.dispatcher.register("file")
@File.register("file")
@dataclass
class InternalFile(Concrete):
    url: str
    expiry_time: datetime

    def serialize(self):
        return {
            "type": "file",
            "file": {"url": self.url, "expiry_time": serialize_datetime(self.expiry_time)},
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        return cls(data["file"]["url"], data["file"]["expiry_time"])


@Icon.dispatcher.register("external")
@File.register("external")
@dataclass
class ExternalFile(Concrete):
    url: str
    name: str

    def serialize(self):
        return {"type": "external", "name": self.name, "external": {"url": self.url}}

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
        return cls(data["external"]["url"], "")

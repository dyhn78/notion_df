from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from notion_df.response.misc import Icon


@dataclass
class File(Icon, metaclass=ABCMeta):
    # https://developers.notion.com/reference/file-object
    TYPE: ClassVar = 'file'


@dataclass
class InternalFile(File):
    url: str
    expiry_time: datetime

    def _plain_serialize(self):
        return {
            "type": "file",
            "file": {
                "url": self.url,
                "expiry_time": self.expiry_time
            }
        }


@dataclass
class ExternalFile(File):
    url: str

    def _plain_serialize(self):
        return {
            "type": "external",
            "external": {
                "url": self.url
            }
        }

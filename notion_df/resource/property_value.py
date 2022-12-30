from abc import ABCMeta
from dataclasses import dataclass
from typing import Any, ClassVar

from notion_df.resource.common import DateValue
from notion_df.resource.core import TypedResource


@dataclass
class PropertyValue(TypedResource, metaclass=ABCMeta):
    # https://developers.notion.com/reference/page-property-values
    id: str
    name: str
    type: ClassVar[str]

    def serialize_plain(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
        }


@dataclass
class DatePropertyValue(PropertyValue):
    type = 'date'
    date: DateValue

    def serialize_plain(self) -> dict[str, Any]:
        return {
            self.type: self.date
        }

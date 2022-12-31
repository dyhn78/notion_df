from abc import ABCMeta
from dataclasses import dataclass
from typing import Any, ClassVar

from notion_df.resource.core import TypedResource
from notion_df.resource.misc import DateRange


@dataclass
class PropertyValue(TypedResource, metaclass=ABCMeta):
    # https://developers.notion.com/reference/page-property-values
    id: str
    name: str
    type: ClassVar[str]

    def plain_serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
        }


@dataclass
class DatePropertyValue(PropertyValue):
    type = 'date'
    date: DateRange

    def plain_serialize(self) -> dict[str, Any]:
        return {
            self.type: self.date
        }

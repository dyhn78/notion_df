from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, final

from notion_df.resource.core import TypedResource


@dataclass
class Property(TypedResource, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-object
    id: str
    name: str
    type: ClassVar[str]

    @final
    def serialize_plain(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            self.type: self._serialize_inner_value()
        }

    @abstractmethod
    def _serialize_inner_value(self):
        pass


@dataclass
class TitleProperty(Property):
    type = 'title'

    def _serialize_inner_value(self):
        return {}

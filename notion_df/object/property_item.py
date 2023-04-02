from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, cast

from typing_extensions import Self

from notion_df.object.core import Deserializable
from notion_df.util.collection import FinalClassDict


@dataclass
class PageProperty(Deserializable, metaclass=ABCMeta):
    """
    represents two types of data structure.

    - partial property item - user side
    - property item - server side

    property item has additional fields, `name` and `id`. these are hidden from __init__() to prevent confusion.

    https://developers.notion.com/reference/page-property-values
    """
    type: str
    name: str = field(init=False)
    id: str = field(init=False)

    @classmethod
    @abstractmethod
    def _eligible_property_types(cls) -> list[str]:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        for property_type in cls._eligible_property_types():
            page_property_by_property_type_dict[property_type] = cls

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self._plain_serialize_type_object(),
        }

    @abstractmethod
    def _plain_serialize_type_object(self) -> dict[str, Any]:
        """https://developers.notion.com/reference/page-property-values#type-objects"""
        pass

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != PageProperty:
            self = super().deserialize(serialized)
        else:
            property_type = serialized['type']
            item_type = page_property_by_property_type_dict[property_type]
            self = item_type.deserialize(serialized)
        self = cast(Self, self)
        self.name = serialized['name']
        self.id = serialized['id']
        return self


page_property_by_property_type_dict = FinalClassDict[str, type[PageProperty]]()

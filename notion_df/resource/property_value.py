from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from notion_df.resource.core import Deserializable, set_master
from notion_df.resource.misc import DateRange


@set_master
@dataclass
class PropertyValue(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/page-property-values
    id: str
    name: str
    type: ClassVar[str]

    def __init_subclass__(cls, **kwargs):
        if cls._skip_init_subclass():
            return
        cls.type = cls._get_type()
        super().__init_subclass__(**kwargs)

    @classmethod
    @abstractmethod
    def _get_type(cls) -> str:
        pass

    def plain_serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            self.type: self._plain_serialize_inner_value()
        }

    @abstractmethod
    def _plain_serialize_inner_value(self):
        pass


@dataclass
class DatePropertyValue(PropertyValue):
    date: DateRange

    @classmethod
    def _get_type(cls) -> str:
        return 'date'

    def _plain_serialize_inner_value(self):
        return self.date
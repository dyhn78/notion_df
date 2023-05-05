from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field

from notion_df.object.database import PlainDatabaseProperty, DatabaseProperty
from notion_df.object.filter import (
    TextFilterPredicate, PropertyFilter, DateFilterPredicate,
    PeopleFilterPredicate, FilterPredicate
)
from notion_df.util.collection import FinalClassDict

property_registry: FinalClassDict[str, type[Property]] = FinalClassDict()


@dataclass
class Property(metaclass=ABCMeta):
    """https://developers.notion.com/reference/property-object"""
    name: str
    id: str = field(init=False, default=None)

    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return
        property_registry[cls.get_typename()] = cls

    @property
    @abstractmethod
    def filter(self) -> FilterPredicate[PropertyFilter]:
        pass

    def _filter_builder(self, filter_type: dict) -> PropertyFilter:
        """helper class to define filter()."""
        return PropertyFilter(filter_type, self.name, self.get_typename())

    @abstractmethod
    def get_database_property(self, **kwargs) -> DatabaseProperty:
        pass


@dataclass
class PlainProperty(Property, metaclass=ABCMeta):
    def get_database_property(self):
        return PlainDatabaseProperty(self.name, self.get_typename())


@dataclass
class TitleProperty(PlainProperty):
    @classmethod
    def get_typename(cls) -> str:
        return 'title'

    @property
    def filter(self) -> TextFilterPredicate[PropertyFilter]:
        return TextFilterPredicate(self._filter_builder)


@dataclass
class RichTextProperty(PlainProperty):
    @classmethod
    def get_typename(cls) -> str:
        return 'rich_text'

    @property
    def filter(self) -> TextFilterPredicate[PropertyFilter]:
        return TextFilterPredicate(self._filter_builder)


@dataclass
class DateProperty(PlainProperty):
    @classmethod
    def get_typename(cls) -> str:
        return 'date'

    @property
    def filter(self) -> DateFilterPredicate[PropertyFilter]:
        return DateFilterPredicate(self._filter_builder)


@dataclass
class PeopleProperty(PlainProperty):
    @classmethod
    def get_typename(cls) -> str:
        return 'people'

    @property
    def filter(self) -> PeopleFilterPredicate[PropertyFilter]:
        return PeopleFilterPredicate(self._filter_builder)

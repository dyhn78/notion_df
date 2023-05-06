from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass

from notion_df.object.filter import (
    TextFilterTypeBuilder, PropertyFilterType, DateFilterTypeBuilder,
    PeopleFilterTypeBuilder, FilterTypeBuilder
)
from notion_df.util.collection import FinalClassDict

property_type_registry: FinalClassDict[str, type[PropertyType]] = FinalClassDict()


@dataclass
class PropertyType(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return
        property_type_registry[cls.get_typename()] = cls

    @property
    @abstractmethod
    def filter(self) -> FilterTypeBuilder[PropertyFilterType]:
        pass

    def _filter_builder(self, filter_type: dict) -> PropertyFilterType:
        """helper class to define filter()."""
        return PropertyFilterType(filter_type, self.get_typename())


@dataclass
class TitlePropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'title'

    @property
    def filter(self) -> TextFilterTypeBuilder[PropertyFilterType]:
        return TextFilterTypeBuilder(self._filter_builder)


@dataclass
class RichTextPropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'rich_text'

    @property
    def filter(self) -> TextFilterTypeBuilder[PropertyFilterType]:
        return TextFilterTypeBuilder(self._filter_builder)


@dataclass
class DatePropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'date'

    @property
    def filter(self) -> DateFilterTypeBuilder[PropertyFilterType]:
        return DateFilterTypeBuilder(self._filter_builder)


@dataclass
class PeoplePropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'people'

    @property
    def filter(self) -> PeopleFilterTypeBuilder[PropertyFilterType]:
        return PeopleFilterTypeBuilder(self._filter_builder)

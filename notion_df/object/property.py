from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import MutableMapping
from typing import TypeVar, Generic, Any, Iterator, Optional

from typing_extensions import Self

from notion_df.object.filter import (
    FilterBuilder
)
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfKeyError, NotionDfAttributeError
from notion_df.util.serialization import DualSerializable, serialize

PropertyValue_T = TypeVar('PropertyValue_T')
property_key_registry: FinalClassDict[str, type[PropertyKey]] = FinalClassDict()


class PropertyKey(DualSerializable, metaclass=ABCMeta):
    typename: str
    database: type[DatabasePropertyValue]
    page: type[PagePropertyValue]

    def __init__(self, name: str):
        self.name = name
        self.id = None

    def __init_subclass__(cls, **kwargs):
        try:
            cls.typename, cls.database, cls.page
        except AttributeError:
            raise NotionDfAttributeError('required class attributes are not defined', {'cls': cls})

    @abstractmethod
    def filter(self) -> FilterBuilder:
        pass


class Properties(DualSerializable, MutableMapping[PropertyKey, PropertyValue_T],
                 Generic[PropertyValue_T], metaclass=ABCMeta):
    key_by_id: dict[str, PropertyValue_T]
    key_by_name: dict[str, PropertyValue_T]

    def __init__(self, items: dict[PropertyKey, PropertyValue_T] = ()):
        self.items = items
        self.key_by_id = {}
        self.key_by_name = {}
        for key, value in items.items():
            self[key] = value

    def serialize(self) -> dict[str, Any]:
        return {key.name: serialize(value) for key, value in self.items.items()}

    def __repr__(self):
        return f'{type(self).__name__}({set(self.key_by_name.keys())})'

    def __iter__(self) -> Iterator[PropertyValue_T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def _get_key(self, key: str | PropertyKey) -> PropertyKey:
        if isinstance(key, str):
            if key in self.key_by_id:
                return self.key_by_id[key]
            return self.key_by_name[key]
        if isinstance(key, PropertyKey):
            return key
        raise NotionDfKeyError('bad key', {'key': key})

    def __getitem__(self, key: str | PropertyKey) -> PropertyValue_T:
        return self.items[self._get_key(key)]

    def get(self, key: str | PropertyKey, default: Optional[PropertyValue_T] = None) -> Optional[PropertyValue_T]:
        key = self._get_key(key)
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: str | PropertyKey, value: PropertyValue_T) -> None:
        self.key_by_id[key.id] = key
        self.key_by_name[key.name] = key
        self.items[key] = value

    def __delitem__(self, key: str | PropertyKey) -> None:
        key = self._get_key(key)
        self.key_by_name.pop(key.name)
        self.key_by_id.pop(key.id)
        self.items.pop(key)


class DatabasePropertyValue(DualSerializable, metaclass=ABCMeta):
    pass


class DatabaseProperties(Properties[DatabasePropertyValue]):
    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in serialized.items():
            typename = prop_serialized['type']
            property_key_cls = property_key_registry[typename]
            property_key = property_key_cls(prop_name)
            property_key.id = prop_serialized['id']
            property_value = property_key.database.deserialize(prop_serialized[typename])
            self[property_key] = property_value
        return self


class PagePropertyValue(DualSerializable, metaclass=ABCMeta):
    pass


class PageProperties(Properties[PagePropertyValue]):
    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in serialized.items():
            typename = prop_serialized['type']
            property_key_cls = property_key_registry[typename]
            property_key = property_key_cls(prop_name)
            property_key.id = prop_serialized['id']
            property_value = property_key.page.deserialize(prop_serialized[typename])
            self[property_key] = property_value
        return self

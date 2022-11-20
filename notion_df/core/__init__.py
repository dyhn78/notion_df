from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Any, TypeVar, Generic, Optional, Type, Final, overload, Iterable, Mapping, final, Iterator

from typing_extensions import Self

from notion_df.util import NotionZapException
from notion_df.util.collection import DictView

Entity_T = TypeVar('Entity_T', bound='Entity', covariant=True)  # TODO: is 'covariant' option really needed?
Field_T = TypeVar('Field_T', bound='Field')
Property_T = TypeVar('Property_T', bound='Property')
Value_T = TypeVar('Value_T', covariant=True)
ValueInput_T = TypeVar('ValueInput_T')


class Entity(Generic[Entity_T]):
    """
    the entity represents the concrete objects - for example workspaces, blocks, users, and comments.

    custom entity class is useful to describe a detailed blueprint of your workspaces structure.
    otherwise if you want to keep it small, use generic class with functional API.
    """

    def __init__(self):
        self.field_set: set[Field[Self, Value_T, ValueInput_T]] = set()
        self.property_dict: dict[str, Property_T] = {}  # property_name to property

    def __init_subclass__(cls, **kwargs):
        ...

    @overload
    def __getitem__(self, key: Field[Self, Value_T, Any]) -> Value_T:
        ...

    def __getitem__(self, key):
        if isinstance(field := key, Field):
            return field.__get__(self, type(self))
        raise KeyError(self, key)

    @overload
    def get(self, key: Field[Self, Value_T, Any], default=None) -> Value_T:
        ...

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    @property
    @abstractmethod
    def pk(self) -> str:
        pass


class EntityProperties(Generic[Entity_T]):
    def __init__(self, entity: Entity_T):
        self.entity: Final = entity


class EntityFields(Generic[Entity_T]):
    def __init__(self, entity: Entity_T):
        self.entity: Final = entity


class Field(Generic[Entity_T, Value_T, ValueInput_T]):
    """
    the 'field' is a logical abstraction of entity's information.
    - fields whose data is directly provided by Notion API
      - property: `title`, `contents`, `Database schema`, {page properties defined on parent's schema}
      - metadata: `id`, `url`, `archived`, `created time`
    - user-defined fields
      - processed data combining one or more properties
      - solely arbitrary flags/labels

    use MutableField to use both __get__() and __set__() methods.
    """

    def __init__(self, default_value_input: ValueInput_T = None):  # TODO: fix argument more universal
        """
        None default_value means there is no default value.
        remind that you cannot actually store null value on Notion.
        """
        self.default_value: Optional[Value_T] = self._parse_value(default_value_input)
        self.entity_types: set[Type[Entity_T]] = set()
        self.listeners: list[FieldEventListener] = []

        from notion_df.core.field_index import (
            FieldIndex, FieldInvertedIndexAll, FieldInvertedIndexFirst, FieldInvertedIndexLast)
        self.index: DictView[Entity_T, Value_T] = FieldIndex(self).view
        self.inverted_index_all: DictView[Value_T, list[Entity_T]] = FieldInvertedIndexAll(self).view
        self.inverted_index_first: DictView[Value_T, Entity_T] = FieldInvertedIndexFirst(self).view
        self.inverted_index_last: DictView[Value_T, Entity_T] = FieldInvertedIndexLast(self).view

    def __set_name__(self, entity: Entity_T, alias: str):
        entity.field_set.add(self)
        # TODO: discover the required (one or more) properties; if not exists, make new one. then bind itself to them.

    @overload
    def __get__(self, entity: None, entity_type: Type[Entity_T]) -> Self:
        ...

    @overload
    def __get__(self, entity: Entity_T, entity_type: Type[Entity_T]) -> Value_T:
        ...

    def __get__(self, instance, owner):
        if instance is None:
            return self
        entity: Entity_T = instance
        if not any(isinstance(entity, entity_type) for entity_type in self.entity_types):
            raise FieldNotBoundError(type(entity).__name__, entity.fields, type(self).__name__)
        if self.default_value is None:
            return self._get_value(entity)
        else:
            try:
                return self._get_value(entity)
            except NotionZapException:  # TODO: error class
                return self.default_value

    @abstractmethod
    def _get_value(self, entity: Entity_T) -> Value_T:
        pass

    @final
    def _set(self, entity: Entity_T, value_input: ValueInput_T) -> None:
        value = self._parse_value(value_input)
        try:
            if self._get_value(entity) == value:
                return
        except NotionZapException:
            pass
        self._set_value(entity, value)
        for listener in self.listeners:
            listener.update({entity: value})

    @abstractmethod
    def _set_value(self, entity: Entity_T, value: Value_T) -> None:
        pass

    @abstractmethod
    def _parse_value(self, value_input: ValueInput_T) -> Value_T:
        if value_input is None:
            return self.default_value
        return value_input


class MutableField(Generic[Entity_T, Value_T, ValueInput_T], Field, metaclass=ABCMeta):
    def __set__(self, entity: Entity_T, value_input: ValueInput_T) -> None:
        self._set(entity, value_input)


class Property(Field[Entity_T, Value_T, ValueInput_T], metaclass=ABCMeta):
    def __init__(self, name: str, default_value_input: ValueInput_T = None):
        super().__init__(default_value_input)
        self.name = name

    def __set_name__(self, entity: Entity_T, alias: str):
        super().__set_name__(entity, alias)
        entity.property_dict[self.name] = self


class MutableProperty(Property[Entity_T, Value_T, ValueInput_T],
                      MutableField[Entity_T, Value_T, ValueInput_T], metaclass=ABCMeta):
    pass


class FieldEventListener(Generic[Entity_T, Value_T], metaclass=ABCMeta):
    def __init__(self, field: Field[Entity_T, Value_T, Any]):
        self.field: Final = field

    @abstractmethod
    def update(self, items: Mapping[Entity_T, Value_T] | Iterable[tuple[Entity_T, Value_T]]):
        pass

    def _fetch(self) -> Iterator[tuple[Entity_T, Value_T]]:
        for entity_type in self.field.entity_types:
            for entity in entity_type.instances:
                yield entity, self.field.__get__(entity, entity_type)


class FieldTypeError(NotionZapException):
    """this field type is not supported for the entity type."""  # TODO: entity 가 field_type 을 검증

    def __init__(self, entity_name: str, field_key: str, field_type_name: Field):
        self.args = self._set_args(entity=entity_name, field_name=field_type_name, field_key=field_key)


class FieldNotBoundError(NotionZapException):
    """this field is not bound on the entity."""

    def __init__(self, entity_name: str, fields: Iterable[Field], field_type_name: str):
        self.args = self._set_args(entity=entity_name, field_keys=fields, field_type_name=field_type_name)

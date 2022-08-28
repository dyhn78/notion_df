from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from typing import Type, Any, TypeVar, Generic, Optional


class EntityMeta(type):
    def __new__(mcs, name, bases, namespace: dict[str, Any]):
        cls = type.__new__(mcs, name, bases, namespace)
        return cls

    ...


class Entity(metaclass=EntityMeta):
    @property
    @abstractmethod
    def pk(self) -> str:
        pass


T_Entity = TypeVar('T_Entity', bound=Entity, covariant=True)  # TODO: is 'covariant' option really needed?
T_FieldValue = TypeVar('T_FieldValue', covariant=True)
T_FieldValueInput = TypeVar('T_FieldValueInput')


class Field(Generic[T_Entity, T_FieldValue, T_FieldValueInput]):
    def __init__(self, *, default_value: T_FieldValueInput = None, entity_type: Type[T_Entity] = Entity):
        """None default_value means no default field_value_input. 
        remind that you cannot actually store null field_value_input on Notion."""  # TODO: better documentation
        self.default_value: Optional[T_FieldValue] = self._read_field_value(default_value)
        self.entity_type: Type[T_Entity] = entity_type
        self.index: dict[T_Entity, T_FieldValue] = {}
        self._inverted_index_dict: dict[str, InvertedIndex[T_Entity, T_FieldValue]] = {}

    def __get__(self, entity: Optional[T_Entity], entity_type: Type[T_Entity]) -> T_FieldValue:
        if entity is None:
            return self.default_value
        else:
            if self.default_value is None:
                return self.index[entity]
            else:
                return self.index.get(entity, self.default_value)

    def __set__(self, entity: Optional[T_Entity], field_value_input: T_FieldValueInput) -> None:
        field_value = self._read_field_value(field_value_input)
        if entity is None:
            self.default_value = field_value
        else:
            if self.index[entity] == field_value != self.default_value:
                return
            self.index[entity] = field_value
            for inverted_index in self._inverted_index_dict.values():
                inverted_index.update((entity, field_value))

    @classmethod
    @abstractmethod
    def _read_field_value(cls, field_value_input: T_FieldValueInput) -> T_FieldValue:
        return field_value_input

    @property
    def inverted_index_all(self) -> InvertedIndexAll[T_Entity, T_FieldValue]:
        """initiate the inverted index if there isn't. otherwise return from cache."""
        return self._inverted_index_dict.get('all', InvertedIndexAll(self))

    @property
    def inverted_index_first(self) -> InvertedIndexFirst[T_Entity, T_FieldValue]:
        return self._inverted_index_dict.get('first', InvertedIndexFirst(self))

    @property
    def inverted_index_last(self) -> InvertedIndexLast[T_Entity, T_FieldValue]:
        return self._inverted_index_dict.get('last', InvertedIndexLast(self))

    @property
    def ii_all(self) -> InvertedIndexAll[T_Entity, T_FieldValue]:
        """alias of get_inverted_index_all()"""
        return self.inverted_index_all

    @property
    def ii_first(self) -> InvertedIndexFirst[T_Entity, T_FieldValue]:
        """alias of get_inverted_index_first()"""
        return self.inverted_index_first

    @property
    def ii_last(self) -> InvertedIndexLast[T_Entity, T_FieldValue]:
        """alias of get_inverted_index_last()"""
        return self.inverted_index_last


class InvertedIndex(Generic[T_Entity, T_FieldValue]):
    def __init__(self, field: Field):
        self.field = field

    @abstractmethod
    def update(self, *entity_to_value: tuple[T_Entity, T_FieldValue]):
        pass

    @abstractmethod
    def __getitem__(self, item: T_FieldValue):
        pass


class InvertedIndexAll(InvertedIndex, Generic[T_Entity, T_FieldValue]):
    def __init__(self, field: Field):
        super().__init__(field)
        self._data: dict[T_FieldValue, set[T_Entity]] = defaultdict(set)

    def update(self, *entity_to_value: tuple[T_Entity, T_FieldValue]) -> None:
        for entity, value in entity_to_value:
            self._data[value].add(entity)

    def __getitem__(self, item: T_FieldValue) -> set[T_Entity]:
        return self._data.__getitem__(item)


class InvertedIndexFirst(InvertedIndex, Generic[T_Entity, T_FieldValue]):
    def __init__(self, field: Field):
        super().__init__(field)
        self._data: dict[T_FieldValue, T_Entity] = {}

    def update(self, *entity_to_value: tuple[T_Entity, T_FieldValue]) -> None:
        for entity, value in entity_to_value:
            if value not in self._data:
                self._data[value] = entity

    def __getitem__(self, item: T_FieldValue) -> T_Entity:
        return self._data.__getitem__(item)


class InvertedIndexLast(InvertedIndex, Generic[T_Entity, T_FieldValue]):
    def __init__(self, field: Field):
        super().__init__(field)
        self._data: dict[T_FieldValue, T_Entity] = {}

    def update(self, *entity_to_value: tuple[T_Entity, T_FieldValue]) -> None:
        for entity, value in entity_to_value:
            self._data[value] = entity
        self._data.update()

    def __getitem__(self, value: T_FieldValue) -> T_Entity:
        return self._data.__getitem__(value)

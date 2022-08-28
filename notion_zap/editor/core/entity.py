from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from typing import Type, Any, cast, TypeVar, Generic, Optional, Iterable


class EntityMeta(type):
    def __new__(mcs, name, bases, namespace: dict[str, Any]):
        cls = cast(Type[TEntity], type.__new__(mcs, name, bases, namespace))
        return cls


class Entity(metaclass=EntityMeta):
    @property
    @abstractmethod
    def pk(self) -> str:
        pass


TEntity = TypeVar('TEntity', bound=Entity)
TFieldValue = TypeVar('TFieldValue')


class Field(Generic[TEntity, TFieldValue]):
    def __init__(self, default_value: Optional[TFieldValue] = None):
        """None default_value means no default value. 
        remind that you cannot actually store null value on Notion."""  # TODO: better documentation
        self.default_value: Optional[TFieldValue] = default_value
        self.index: dict[TEntity, TFieldValue] = {}
        self._inverted_index_dict: dict[str, InvertedIndex[TEntity, TFieldValue]] = {}

    def __get__(self, entity: Optional[TEntity], entity_type: Type[TEntity]) -> TFieldValue:
        if entity is None:
            return self.default_value
        else:
            if self.default_value is None:
                return self.index[entity]
            else:
                return self.index.get(entity, self.default_value)

    def __set__(self, entity: Optional[TEntity], value: TFieldValue):
        if entity is None:
            self.default_value = value
        else:
            self.index[entity] = value
            for inverted_index in self._inverted_index_dict.values():
                inverted_index.update((entity, value))

    @property
    def inverted_index_all(self) -> InvertedIndexAll[TEntity, TFieldValue]:
        return self._inverted_index_dict.get('all', InvertedIndexAll(self))

    @property
    def inverted_index_first(self) -> InvertedIndexFirst[TEntity, TFieldValue]:
        return self._inverted_index_dict.get('first', InvertedIndexFirst(self))

    @property
    def inverted_index_last(self) -> InvertedIndexLast[TEntity, TFieldValue]:
        return self._inverted_index_dict.get('last', InvertedIndexLast(self))

    @property
    def ii_all(self) -> InvertedIndexAll[TEntity, TFieldValue]:
        return self.inverted_index_all

    @property
    def ii_first(self) -> InvertedIndexFirst[TEntity, TFieldValue]:
        return self.inverted_index_first

    @property
    def ii_last(self) -> InvertedIndexLast[TEntity, TFieldValue]:
        return self.inverted_index_last


class InvertedIndex(Generic[TEntity, TFieldValue]):
    def __init__(self, field: Field[TEntity, TFieldValue]):
        self.field = field

    @abstractmethod
    def update(self, *entity_value_tuple: Iterable[tuple[TEntity, TFieldValue]]):
        pass

    @abstractmethod
    def __getitem__(self, item: TFieldValue):
        pass


class InvertedIndexAll(InvertedIndex[TEntity, TFieldValue]):
    def __init__(self, field: Field[TEntity, TFieldValue]):
        super().__init__(field)
        self._data: dict[TFieldValue, set[TEntity]] = defaultdict(set)

    def update(self, *entity_value_tuple: Iterable[tuple[TEntity, TFieldValue]]) -> None:
        for entity, value in entity_value_tuple:
            self._data[value].add(entity)

    def __getitem__(self, item: TFieldValue) -> set[TEntity]:
        return self._data.__getitem__(item)


class InvertedIndexFirst(InvertedIndex[TEntity, TFieldValue]):
    def __init__(self, field: Field[TEntity, TFieldValue]):
        super().__init__(field)
        self._data: dict[TFieldValue, TEntity] = {}

    def update(self, *entity_value_tuple: Iterable[tuple[TEntity, TFieldValue]]) -> None:
        for entity, value in entity_value_tuple:
            if value not in self._data:
                self._data[value] = entity

    def __getitem__(self, item: TFieldValue) -> TEntity:
        return self._data.__getitem__(item)


class InvertedIndexLast(InvertedIndex[TEntity, TFieldValue]):
    def __init__(self, field: Field[TEntity, TFieldValue]):
        super().__init__(field)
        self._data: dict[TFieldValue, TEntity] = {}

    def update(self, *entity_value_tuple: Iterable[tuple[TEntity, TFieldValue]]) -> None:
        for entity, value in entity_value_tuple:
            self._data[value] = entity
        self._data.update()

    def __getitem__(self, value: TFieldValue) -> TEntity:
        return self._data.__getitem__(value)

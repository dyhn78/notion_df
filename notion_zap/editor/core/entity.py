from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from typing import Type, Any, cast, TypeVar, Generic, Optional


class EntityMeta(type):
    def __new__(mcs, name, bases, namespace: dict[str, Any]):
        cls = cast(Type[Entity], type.__new__(mcs, name, bases, namespace))
        return cls


class BaseEntity(metaclass=EntityMeta):
    @property
    @abstractmethod
    def pk(self) -> str:
        pass


Entity = TypeVar('Entity', bound=BaseEntity)
FieldValue = TypeVar('FieldValue')


class BaseField(Generic[Entity, FieldValue]):
    def __init__(self, default_value: Optional[FieldValue] = None):
        """None default_value means no default value. 
        remind that you cannot actually store null value on Notion."""  # TODO: better documentation
        self.default_value: Optional[FieldValue] = default_value
        self.index: dict[Entity, FieldValue] = {}
        self._inverted_index_dict: dict[str, InvertedIndex] = {}

    def __get__(self, entity: Optional[Entity], entity_type: Type[Entity]) -> FieldValue:
        if entity is None:
            return self.default_value
        else:
            if self.default_value is None:
                return self.index[entity]
            else:
                return self.index.get(entity, self.default_value)

    def __set__(self, entity: Optional[Entity], value: FieldValue):
        if entity is None:
            self.default_value = value
        else:
            self.index[entity] = value
            for inverted_index in self._inverted_index_dict.values():
                inverted_index.update(entity, value)

    @property
    def inverted_index_all(self):
        return self._inverted_index_dict.get('all', InvertedIndexAll(self))

    @property
    def inverted_index_first(self):
        return self._inverted_index_dict.get('first', InvertedIndexFirst(self))

    @property
    def inverted_index_last(self):
        return self._inverted_index_dict.get('last', InvertedIndexLast(self))


class InvertedIndex(Generic[Entity, FieldValue]):
    registry: dict[BaseField, dict[Type[InvertedIndex], InvertedIndex]] = defaultdict(dict)

    def __init__(self, field: BaseField[FieldValue, Entity]):
        self.field = field

    @abstractmethod
    def update(self, entity: Entity, value: FieldValue):
        pass


class InvertedIndexAll(InvertedIndex):
    def __init__(self, field: BaseField[FieldValue, Entity]):
        super().__init__(field)
        self.data: dict[FieldValue, set[Entity]] = defaultdict(set)

    def update(self, entity: Entity, value: FieldValue):
        self.data[value].add(entity)


class InvertedIndexFirst(InvertedIndex):
    def __init__(self, field: BaseField[FieldValue, Entity]):
        super().__init__(field)
        self.data: dict[FieldValue, Entity] = {}

    def update(self, entity: Entity, value: FieldValue):
        if value not in self.data:
            self.data[value] = entity


class InvertedIndexLast(InvertedIndex):
    def __init__(self, field: BaseField[FieldValue, Entity]):
        super().__init__(field)
        self.data: dict[FieldValue, Entity] = {}

    def update(self, entity: Entity, value: FieldValue):
        self.data[value] = entity

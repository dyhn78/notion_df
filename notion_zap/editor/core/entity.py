from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from typing import Type, Any, TypeVar, Generic, Optional, Literal

from notion_zap.editor.core.utils import repr_object


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

    def base(self):
        return EntityBaseView(self)


T_Entity = TypeVar('T_Entity', bound=Entity, covariant=True)  # TODO: is 'covariant' option really needed?
T_FieldValue = TypeVar('T_FieldValue', covariant=True)
T_FieldValueInput = TypeVar('T_FieldValueInput')


class EntityBaseView(Generic[T_Entity]):
    """represents the server-side status."""

    def __init__(self, entity: T_Entity):
        self.entity = entity

    ...


# TODO: separate field/field_index; Field.dual(...) -> tuple(Field, Field)
class Field(Generic[T_Entity, T_FieldValue, T_FieldValueInput]):
    def __init__(self, _default_value: T_FieldValueInput = None):
        """
        - default_value: None default_value means there is no default value.
        remind that you cannot actually store null value on Notion.
        - index_base: represents the server-side status. naming inspired by git 'base commit'.
        - index_head: represents the latest status, both the server-side and the local modification.
        """
        self.default_value: Optional[T_FieldValue] = self.read_value(_default_value)
        self.index_base: dict[T_Entity, T_FieldValue] = {}
        self.index_head: dict[T_Entity, T_FieldValue] = {}
        self._inverted_index_base: Optional[InvertedIndexMulti[T_Entity, T_FieldValue]] = None
        self._inverted_index_head: Optional[InvertedIndexMulti[T_Entity, T_FieldValue]] = None

    def __get__(self, _entity: Optional[T_Entity | EntityBaseView[T_Entity]],
                entity_type: Type[T_Entity]) -> T_FieldValue:
        if _entity is None:
            return self.default_value
        elif isinstance(_entity, EntityBaseView):
            entity = _entity.entity
            if self.default_value is None:
                return self.index_base[entity]
            else:
                return self.index_base.get(entity, self.default_value)
        elif isinstance(_entity, Entity):
            entity = _entity
            if self.default_value is None:
                return self.index_head[entity]
            else:
                return self.index_head.get(entity, self.default_value)

    def __set__(self, entity: T_Entity, _field_value: T_FieldValueInput) -> None:
        field_value = self.read_value(_field_value)
        if self.index_head[entity] == field_value != self.default_value:
            return
        if entity not in self.index_base:
            self.index_base[entity] = field_value
        self.index_head[entity] = field_value
        self.inverted_index_head.update((entity, field_value))

    def clear(self):
        self.index_base = self.index_head = self._inverted_index_base = self._inverted_index_head = {}

    def sync(self):
        self.index_base = self.index_head
        self._inverted_index_base = self._inverted_index_head

    @classmethod
    @abstractmethod
    def read_value(cls, _field_value: T_FieldValueInput) -> T_FieldValue:
        return _field_value

    @property
    def inverted_index_base(self) -> InvertedIndexMulti[T_Entity, T_FieldValue]:
        if not (ii := self._inverted_index_base):
            self._inverted_index_base = InvertedIndexMulti(self)
        return ii

    @property
    def inverted_index_head(self) -> InvertedIndexMulti[T_Entity, T_FieldValue]:
        if not (ii := self._inverted_index_head):
            self._inverted_index_head = InvertedIndexMulti(self)
        return ii

    @property
    def ii_base(self) -> InvertedIndexMulti[T_Entity, T_FieldValue]:
        """alias of inverted_index_base()"""
        return self.inverted_index_base

    @property
    def ii_head(self) -> InvertedIndexMulti[T_Entity, T_FieldValue]:
        """alias of inverted_index_head()"""
        return self.inverted_index_head


class InvertedIndexMulti(Generic[T_Entity, T_FieldValue]):
    def __init__(self, field: Field):
        self.field = field
        self._data: dict[T_FieldValue, list[T_Entity]] = defaultdict(list)

    def __repr__(self) -> str:
        return repr_object(self, field=type(self.field).__name__, data=self._data)

    def __getitem__(self, field_value: T_FieldValue) -> list[T_Entity]:
        return self._data.__getitem__(field_value)

    def update(self, *entity_to_value: tuple[T_Entity, T_FieldValue]):
        for entity, value in entity_to_value:
            self._data[value].append(entity)

    @property
    def first(self) -> InvertedIndexUnique[T_Entity, T_FieldValue]:
        return InvertedIndexUnique(self.field, self._data, 'first')

    @property
    def last(self) -> InvertedIndexUnique[T_Entity, T_FieldValue]:
        return InvertedIndexUnique(self.field, self._data, 'last')

    def clear(self):
        self._data.clear()


class InvertedIndexUnique(Generic[T_Entity, T_FieldValue]):
    def __init__(self, field: Field, _data: dict[T_FieldValue, list[T_Entity]], position: Literal['first', 'last']):
        super().__init__()
        self.field = field
        self._data: dict[T_FieldValue, list[T_Entity]] = _data
        self.position = 0 if position == 'first' else -1

    def __repr__(self) -> str:
        return repr_object(self, field=type(self.field).__name__, data={k: self[k] for k in self._data})

    def __getitem__(self, field_value: T_FieldValue) -> T_Entity:
        return self._data[field_value][self.position]

    def get(self, field_value: T_FieldValue) -> T_Entity | None:
        try:
            return self[field_value]
        except IndexError:
            return None

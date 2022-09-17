from __future__ import annotations

from abc import abstractmethod, ABCMeta
from collections import defaultdict
from typing import Any, TypeVar, Generic, Optional, Type, cast, Literal, Callable

from notion_zap.editor.frame.utils import repr_object

Entity_T = TypeVar('Entity_T', bound='Entity', covariant=True)  # TODO: is 'covariant' option really needed?
EntityAccessKey_T = TypeVar('EntityAccessKey_T')
Field_T = TypeVar('Field_T', bound='Field')
FieldValue_T = TypeVar('FieldValue_T', covariant=True)
FieldValueInput_T = TypeVar('FieldValueInput_T')


class Field(Generic[Entity_T, FieldValue_T, FieldValueInput_T]):
    # TODO: separate field/field_index; Field.dual(...) -> tuple(Field, Field)
    #  make index_head a property
    """
    - default_value: None default_value means there is no default value.
        remind that you cannot actually store null value on Notion.
    """

    def __init__(self, _default_value: FieldValueInput_T = None):
        self.default_value: Optional[FieldValue_T] = self.read_value(_default_value)
        self._index: Optional[dict[Entity_T, FieldValue_T]] = None
        self._inverted_index: Optional[FieldMultiInvertedIndex[Entity_T, FieldValue_T]] = None

    def __get__(self: Field_T, _entity: Optional[Entity_T], entity_type: Type[Entity_T]) -> FieldValue_T | Field_T:
        if _entity is None:
            return self
        entity: Entity_T = _entity
        if self.default_value is None:
            value = self.read_value(entity[self])
        else:
            value = self.read_value(entity.get(self, self.default_value))
        if self._index is not None:
            self._index[entity] = value
        if self._inverted_index is not None:
            self._inverted_index.update((entity, value))
        return value

    def __set__(self, entity: Entity_T, _value: FieldValueInput_T) -> None:
        value = self.read_value(_value)
        if entity[self] == value != self.default_value:
            return
        entity[self] = value
        if self._index is not None:
            self._index[entity] = value
        if self._inverted_index is not None:
            self._inverted_index.update((entity, value))

    @classmethod
    @abstractmethod
    def read_value(cls, _value: FieldValueInput_T) -> FieldValue_T:
        return _value

    @property
    def index(self) -> dict[Entity_T, FieldValue_T]:
        if (index := self._index) is not None:
            self._index = {}
        return index

    @property
    def inverted_index(self) -> FieldMultiInvertedIndex[Entity_T, FieldValue_T]:
        if (inverted_index := self._inverted_index) is not None:
            self._inverted_index = FieldMultiInvertedIndex(self.__class__.__name__, [])  # TODO: pre-existing values
        return inverted_index


class HeadField(Field, metaclass=ABCMeta):
    """
    represents the server-side status. term inspired by git 'base commit'.
    """


class BaseField(Field, metaclass=ABCMeta):
    """
    represents the latest status, both the server-side and the local modification.
    """


class FieldMultiInvertedIndex(Generic[Entity_T, FieldValue_T]):
    # TODO: make field.inverted_index.__setitem__ unavailable from outside (like private method)
    #  - consider "Mapping[.., ..]"?
    def __init__(self, field_name: str, entity_and_value_list: list[tuple[Entity_T, FieldValue_T]]):
        self._field_name = field_name
        self._value_to_entities: dict[FieldValue_T, list[Entity_T]] = defaultdict(list)
        self.update(*entity_and_value_list)

    def __repr__(self) -> str:
        return repr_object(self, field=self._field_name, data=self._value_to_entities)

    def __getitem__(self, field_value: FieldValue_T) -> list[Entity_T]:
        return self._value_to_entities.__getitem__(field_value)

    def update(self, *entity_and_value: tuple[Entity_T, FieldValue_T]):
        for entity, value in entity_and_value:
            self._value_to_entities[value].append(entity)

    def clear(self):
        self._value_to_entities.clear()

    @property
    def first(self) -> FieldUniqueInvertedIndex[Entity_T, FieldValue_T]:
        return FieldUniqueInvertedIndex(self._field_name, self._value_to_entities, 'first')

    @property
    def last(self) -> FieldUniqueInvertedIndex[Entity_T, FieldValue_T]:
        return FieldUniqueInvertedIndex(self._field_name, self._value_to_entities, 'last')


class FieldUniqueInvertedIndex(Generic[Entity_T, FieldValue_T]):
    def __init__(self, field_name: str, _value_to_entities: dict[FieldValue_T, list[Entity_T]],
                 position: Literal['first', 'last']):
        super().__init__()
        self._field_name = field_name
        self._value_to_entities: dict[FieldValue_T, list[Entity_T]] = _value_to_entities
        if position == 'first':
            self._unique_index = 0
        else:
            self._unique_index = -1

    def __repr__(self) -> str:
        return repr_object(self, field=self._field_name, data={k: self[k] for k in self._value_to_entities})

    def __getitem__(self, field_value: FieldValue_T) -> Entity_T:
        return self._value_to_entities[field_value][self._unique_index]

    def get(self, field_value: FieldValue_T) -> Entity_T | None:
        try:
            return self[field_value]
        except IndexError:
            return None


class EntityMeta(type):
    def __new__(mcs, name, bases, namespace: dict[str, Any]):
        for attr_name, attr in namespace.items():
            if isinstance(attr, Field):
                field = cast(Field, attr)
                namespace['_access_funcs'][field] = field.access_func
        return super().__new__(mcs, name, bases, namespace)

    ...


class Entity(Generic[EntityAccessKey_T], metaclass=EntityMeta):
    _access_funcs: dict[Any, Callable[[Entity], Any]] = {}

    @property
    @abstractmethod
    def pk(self) -> str:
        pass

    def __getitem__(self: Entity_T, access_key: EntityAccessKey_T | Field[Entity_T, Any, Any]) -> Any:
        return self._access_funcs[access_key](self)

    def get(self: Entity_T, access_key: EntityAccessKey_T | Field[Entity_T, Any, Any], default=None):
        try:
            return self[access_key]
        except KeyError:
            return default

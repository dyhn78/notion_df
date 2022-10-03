from __future__ import annotations

from abc import abstractmethod, ABCMeta
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, TypeVar, Generic, Optional, Type, Literal, Final, ClassVar, Iterator, overload

from notion_df.utils import repr_object, NotionZapException
from notion_df.utils.dict_view import DictView

Entity_T = TypeVar('Entity_T', bound='Entity', covariant=True)  # TODO: is 'covariant' option really needed?
Field_T = TypeVar('Field_T', bound='MutableField')
FieldValue_T = TypeVar('FieldValue_T', covariant=True)
FieldValueInput_T = TypeVar('FieldValueInput_T')


# TODO
#  - FieldClaim->MutableField 방식으로는 여러 필드 묶음에 대해서 구현 불가능. -> MyBaseBlock.__init_subclass__/__new__()
#  - https://docs.python.org/ko/3/reference/datamodel.html?highlight=__set_name__#object.__set_name__


class Entity:
    """
    the entity represents the concrete objects - for example workspaces, blocks, users, and comments.
    """
    _field_keys: ClassVar[dict[Field, str]] = {}

    def __init__(self):
        pass

    def __init_subclass__(cls, **kwargs):
        for key, attr in cls.__dict__.items():
            if isinstance(attr, Field):
                cls._add_field(attr, key)

    @classmethod
    def _add_field(cls, field: Field, field_key: str) -> None:
        # TODO: check entity_type supports field_type
        cls._field_keys[field] = field_key

    def get_field_key(self: Entity_T & Entity, field: Field[Entity_T, Any, Any]) -> str:
        if field_key := self._field_keys[field]:
            return field_key
        raise FieldNotBoundError(type(self).__name__, self._field_keys, type(field).__name__)

    @overload
    def __getitem__(self: Entity_T & Entity, key: Field[Entity_T, FieldValue_T, Any]) -> FieldValue_T:
        ...

    def __getitem__(self, key):
        if isinstance(field := key, Field):
            field_key = self.get_field_key(field)
            return getattr(self, field_key)
        raise KeyError(self, key)

    @overload
    def get(self: Entity_T & Entity, key: Field[Entity_T, FieldValue_T, Any], default=None) -> FieldValue_T:
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


class Field(Generic[Entity_T, FieldValue_T, FieldValueInput_T]):
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

    def __init__(self, _default_value: FieldValueInput_T = None):
        """
        None default_value means there is no default value.
        remind that you cannot actually store null value on Notion.
        """
        self.default_value: Optional[FieldValue_T] = self.read_value(_default_value)
        self._index: dict[Entity_T, FieldValue_T] = {}
        self._inverted_index = Optional[InvertedIndex[FieldValue_T, Entity_T]] = None

    def __set_name__(self, entity: Entity_T, name: str):
        ...  # TODO

    @overload
    def __get__(self: Field_T & Field, _entity: None, entity_type: Type[Entity_T]) -> Field_T:
        ...

    @overload
    def __get__(self: Field_T & Field, _entity: Entity_T, entity_type: Type[Entity_T]) -> FieldValue_T:
        ...

    def __get__(self, _entity, entity_type):
        if _entity is None:
            return self
        entity: Entity_T = _entity
        if self.default_value is None:
            return self._index[entity]
        else:
            return self._index.get(entity, self.default_value)

    def _set(self, entity: Entity_T, _value: FieldValueInput_T) -> None:
        value = self.read_value(_value)
        if entity in self._index and self._index[entity] == value:
            return
        self._index[entity] = value
        if self._inverted_index is not None:
            self._inverted_index.update({entity: value})

    @abstractmethod
    def read_value(self, _value: FieldValueInput_T) -> FieldValue_T:
        if _value is None:
            return self.default_value
        return _value

    @property
    def index(self) -> DictView[Entity_T, FieldValue_T]:
        return DictView(self._index, type='index', field_type=type(self).__name__)

    def _get_inverted_index(self) -> InvertedIndex[FieldValue_T, Entity_T]:
        if self._inverted_index is None:
            self._inverted_index = InvertedIndex(self._index, type(self).__name__)
        return self._inverted_index

    @property
    def inverted_index_all(self) -> DictView[FieldValue_T, list[Entity_T]]:
        return self._get_inverted_index().view_all

    @property
    def inverted_index_first(self) -> InvertedIndexUnique[FieldValue_T, Entity_T]:
        return self._get_inverted_index().view_first

    @property
    def inverted_index_last(self) -> InvertedIndexUnique[FieldValue_T, Entity_T]:
        return self._get_inverted_index().view_last


class MutableField(Generic[Entity_T, FieldValue_T, FieldValueInput_T], Field, metaclass=ABCMeta):
    def __set__(self, entity: Entity_T, _value: FieldValueInput_T) -> None:
        self._set(entity, _value)


class InvertedIndex(Generic[FieldValue_T, Entity_T]):
    def __init__(self, field_index: Mapping[Entity_T, FieldValue_T], field_type: str):
        self._value_to_entitys: dict[FieldValue_T, list[Entity_T]] = defaultdict(list)
        self.update(field_index)

        self.field_type: Final = field_type
        self.view_all: Final = DictView(self._value_to_entitys, type='inverted_index_all', field_type=self.field_type)
        self.view_first: Final = InvertedIndexUnique(self._value_to_entitys, self.field_type, 'first')
        self.view_last: Final = InvertedIndexUnique(self._value_to_entitys, self.field_type, 'last')

    def update(self, field_index: Mapping[Entity_T, FieldValue_T]) -> None:
        for entity, value in field_index.items():
            self._value_to_entitys[value].append(entity)

    def clear(self) -> None:
        self._value_to_entitys.clear()

    def __repr__(self) -> str:
        return repr_object(self, field_type=self.field_type, data=self._value_to_entitys)


class InvertedIndexUnique(Mapping[FieldValue_T, Entity_T]):
    def __init__(self, _value_to_entitys: dict[FieldValue_T, list[Entity_T]], field_type: str,
                 position: Literal['first', 'last']):
        self._value_to_entitys = _value_to_entitys
        self.field_type: Final = field_type
        self.position: Final = position
        self.position_index: Final = {
            'first': 0, 'last': -1
        }[position]

    def __getitem__(self, field_value: FieldValue_T) -> Entity_T:
        return self._value_to_entitys[field_value][self.position_index]

    def __len__(self) -> int:
        return self._value_to_entitys.__len__()

    def __iter__(self) -> Iterator[FieldValue_T]:
        return self._value_to_entitys.__iter__()

    def __repr__(self) -> str:
        data = {value: self[value] for value in self._value_to_entitys}
        return repr_object(self, type=f'inverted_index_{self.position}', field_type=self.field_type, data=data)


class FieldTypeError(NotionZapException):
    """this field type is not supported for the entity type."""  # TODO: entity 가 entity 을 거쳐 field_type 을 검증

    def __init__(self, entity_name: str, field_key: str, field_type_name: Field):
        self.args = self._set_args(entity=entity_name, field_name=field_type_name, field_key=field_key)


class FieldNotBoundError(NotionZapException):
    """this field is not bound on the entity."""

    def __init__(self, entity_name: str, field_keys: dict[Field, str], field_type_name: str):
        self.args = self._set_args(entity=entity_name, field_keys=field_keys, field_type_name=field_type_name)

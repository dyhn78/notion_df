from __future__ import annotations

from abc import abstractmethod, ABCMeta
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, TypeVar, Generic, Optional, Type, Literal, Final, ClassVar, Iterator, overload, Iterable

from notion_df.utils import repr_object, NotionZapException
from notion_df.utils.dict_view import DictView

Entity_T = TypeVar('Entity_T', bound='Entity', covariant=True)  # TODO: is 'covariant' option really needed?
Model_T = TypeVar('Model_T', bound='Model', covariant=True)
Field_T = TypeVar('Field_T', bound='MutableField')
FieldValue_T = TypeVar('FieldValue_T', covariant=True)
FieldValueInput_T = TypeVar('FieldValueInput_T')


# TODO
#  - FieldClaim->MutableField 방식으로는 여러 필드 묶음에 대해서 구현 불가능. -> MyBaseBlock.__init_subclass__/__new__()
#  - https://docs.python.org/ko/3/reference/datamodel.html?highlight=__set_name__#object.__set_name__


class Entity:
    """
    the entity represents the concrete objects - for example workspaces, blocks, users, and comments.
    custom entity class is useful to describe a detailed blueprint of your workspaces structure.
    otherwise if you want to keep it small, use generic class.
    """

    def __init__(self, models: Iterable[Model]): ...


class Model:
    """
    the model represents the editor routine.  # TODO docs
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

    def get_field_key(self: Model_T & Model, field: Field[Model_T, Any, Any]) -> str:
        if field_key := self._field_keys[field]:
            return field_key
        raise FieldNotBoundError(type(self).__name__, self._field_keys, type(field).__name__)

    @overload
    def __getitem__(self: Model_T & Model, key: Field[Model_T, FieldValue_T, Any]) -> FieldValue_T:
        ...

    def __getitem__(self, key):
        if isinstance(field := key, Field):
            field_key = self.get_field_key(field)
            return getattr(self, field_key)
        raise KeyError(self, key)

    @overload
    def get(self: Model_T & Model, key: Field[Model_T, FieldValue_T, Any], default=None) -> FieldValue_T:
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


class Field(Generic[Model_T, FieldValue_T, FieldValueInput_T]):
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
        self._index: dict[Model_T, FieldValue_T] = {}
        self._inverted_index = Optional[InvertedIndex[FieldValue_T, Model_T]] = None

    def __set_name__(self, model: Model_T, name: str):
        ...  # TODO

    @overload
    def __get__(self: Field_T & Field, _model: None, entity_type: Type[Model_T]) -> Field_T:
        ...

    @overload
    def __get__(self: Field_T & Field, _model: Model_T, entity_type: Type[Model_T]) -> FieldValue_T:
        ...

    def __get__(self, _model, entity_type):
        if _model is None:
            return self
        model: Model_T = _model
        if self.default_value is None:
            return self._index[model]
        else:
            return self._index.get(model, self.default_value)

    def _set(self, model: Model_T, _value: FieldValueInput_T) -> None:
        value = self.read_value(_value)
        if model in self._index and self._index[model] == value:
            return
        self._index[model] = value
        if self._inverted_index is not None:
            self._inverted_index.update({model: value})

    @abstractmethod
    def read_value(self, _value: FieldValueInput_T) -> FieldValue_T:
        if _value is None:
            return self.default_value
        return _value

    @property
    def index(self) -> DictView[Model_T, FieldValue_T]:
        return DictView(self._index, type='index', field_type=type(self).__name__)

    def _get_inverted_index(self) -> InvertedIndex[FieldValue_T, Model_T]:
        if self._inverted_index is None:
            self._inverted_index = InvertedIndex(self._index, type(self).__name__)
        return self._inverted_index

    @property
    def inverted_index_all(self) -> DictView[FieldValue_T, list[Model_T]]:
        return self._get_inverted_index().view_all

    @property
    def inverted_index_first(self) -> InvertedIndexUnique[FieldValue_T, Model_T]:
        return self._get_inverted_index().view_first

    @property
    def inverted_index_last(self) -> InvertedIndexUnique[FieldValue_T, Model_T]:
        return self._get_inverted_index().view_last


class MutableField(Generic[Model_T, FieldValue_T, FieldValueInput_T], Field, metaclass=ABCMeta):
    def __set__(self, model: Model_T, _value: FieldValueInput_T) -> None:
        self._set(model, _value)


class InvertedIndex(Generic[FieldValue_T, Model_T]):
    def __init__(self, field_index: Mapping[Model_T, FieldValue_T], field_type: str):
        self._value_to_models: dict[FieldValue_T, list[Model_T]] = defaultdict(list)
        self.update(field_index)

        self.field_type: Final = field_type
        self.view_all: Final = DictView(self._value_to_models, type='inverted_index_all', field_type=self.field_type)
        self.view_first: Final = InvertedIndexUnique(self._value_to_models, self.field_type, 'first')
        self.view_last: Final = InvertedIndexUnique(self._value_to_models, self.field_type, 'last')

    def update(self, field_index: Mapping[Model_T, FieldValue_T]) -> None:
        for model, value in field_index.items():
            self._value_to_models[value].append(model)

    def clear(self) -> None:
        self._value_to_models.clear()

    def __repr__(self) -> str:
        return repr_object(self, field_type=self.field_type, data=self._value_to_models)


class InvertedIndexUnique(Mapping[FieldValue_T, Model_T]):
    def __init__(self, _value_to_models: dict[FieldValue_T, list[Model_T]], field_type: str,
                 position: Literal['first', 'last']):
        self._value_to_models = _value_to_models
        self.field_type: Final = field_type
        self.position: Final = position
        self.position_index: Final = {
            'first': 0, 'last': -1
        }[position]

    def __getitem__(self, field_value: FieldValue_T) -> Model_T:
        return self._value_to_models[field_value][self.position_index]

    def __len__(self) -> int:
        return self._value_to_models.__len__()

    def __iter__(self) -> Iterator[FieldValue_T]:
        return self._value_to_models.__iter__()

    def __repr__(self) -> str:
        data = {value: self[value] for value in self._value_to_models}
        return repr_object(self, type=f'inverted_index_{self.position}', field_type=self.field_type, data=data)


class FieldTypeError(NotionZapException):
    """this field type is not supported for the entity type."""  # TODO: entity 가 model 을 거쳐 field_type 을 검증

    def __init__(self, entity_name: str, field_key: str, field_type_name: Field):
        self.args = self._set_args(entity=entity_name, field_name=field_type_name, field_key=field_key)


class FieldNotBoundError(NotionZapException):
    """this field is not bound on the entity."""

    def __init__(self, entity_name: str, field_keys: dict[Field, str], field_type_name: str):
        self.args = self._set_args(entity=entity_name, field_keys=field_keys, field_type_name=field_type_name)

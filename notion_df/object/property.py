from __future__ import annotations

import inspect
from abc import ABCMeta
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from datetime import datetime, date
from functools import cache
from typing import ClassVar, TypeVar, Generic, Any, Iterator, Optional, Literal, Union, Iterable, Final, TYPE_CHECKING, \
    get_type_hints

from typing_extensions import Self

from notion_df.object.common import StatusGroups, SelectOption, DateRange
from notion_df.object.constant import RollupFunction, NumberFormat, Number
from notion_df.object.file import Files
from notion_df.object.filter import PropertyFilter, CheckboxFilterBuilder, PeopleFilterBuilder, \
    DateFilterBuilder, TextFilterBuilder, FilesFilterBuilder, NumberFilterBuilder, MultiSelectFilterBuilder, \
    RelationFilterBuilder, SelectFilterBuilder, FilterBuilder, FormulaPropertyFilter
from notion_df.object.rich_text import RichText
from notion_df.object.user import PartialUser, User
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfKeyError, NotionDfValueError
from notion_df.util.misc import repr_object
from notion_df.core.serialization import DualSerializable, deserialize, serialize

if TYPE_CHECKING:
    from notion_df.entity import Page, Database

property_registry: FinalClassDict[str, type[Property]] = FinalClassDict()
PropertyValue_T = TypeVar('PropertyValue_T')
# TODO (low priority): fix that `DatabasePropertyValue_T.bound == DatabasePropertyValue` does not ruin the type hinting
DatabasePropertyValue_T = TypeVar('DatabasePropertyValue_T')
PagePropertyValue_T = TypeVar('PagePropertyValue_T')
FilterBuilder_T = TypeVar('FilterBuilder_T', bound=FilterBuilder)


class Property(Generic[DatabasePropertyValue_T, PagePropertyValue_T, FilterBuilder_T], metaclass=ABCMeta):
    typename: ClassVar[str]
    database_value: type[DatabasePropertyValue_T]
    page_value: type[PagePropertyValue_T]
    _filter_cls: type[FilterBuilder_T]

    def __init__(self, name: str):
        self.name: Final[str] = name
        self.id: Optional[str] = None

    def __repr__(self) -> str:
        return repr_object(self, ['name', 'id'])

    def __eq__(self, other: Property) -> bool:
        if self.name != other.name:
            return False
        if self.id is not None and other.id is not None and self.id != other.id:
            return False
        if not (issubclass(type(self), type(other)) or issubclass(type(other), type(self))):
            return False
        return True

    def __hash__(self):
        return hash(self.name)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            assert cls.typename
        if typename := getattr(cls, 'typename', None):
            property_registry[typename] = cls

    @property
    def filter(self) -> FilterBuilder_T:
        def build(filter_condition: dict[str, Any]):
            return PropertyFilter(self.name, self.typename, filter_condition)

        return self._filter_cls(build)

    # noinspection PyMethodMayBeStatic
    def _serialize_page(self, prop_value: PropertyValue_T) -> dict[str, Any]:
        return serialize(prop_value)

    @classmethod
    def _deserialize_page(cls, prop_serialized: dict[str, Any]) -> PropertyValue_T:
        """allow proxy-deserialization of subclasses."""
        typename = prop_serialized['type']
        if cls == Property:
            subclass = property_registry[typename]
            return subclass._deserialize_page(prop_serialized)
        return deserialize(cls.page_value, prop_serialized[typename])

    @classmethod
    def _deserialize_database(cls, prop_serialized: dict[str, Any]) -> PropertyValue_T:
        """allow proxy-deserialization of subclasses."""
        typename = prop_serialized['type']
        if cls == Property:
            subclass = property_registry[typename]
            return subclass._deserialize_page(prop_serialized)
        return deserialize(cls.database_value, prop_serialized[typename])


class Properties(DualSerializable, MutableMapping[Property, PropertyValue_T], metaclass=ABCMeta):
    _key_by_id: dict[str, Property]
    _key_by_name: dict[str, Property]
    _value_by_name: dict[str, PropertyValue_T]
    _values: dict[Property, PropertyValue_T]

    def __init__(self, items: Optional[dict[Property, PropertyValue_T]] = None):
        self._key_by_id = {}
        self._key_by_name = {}
        self._value_by_name = {}
        self._values = {}
        if not items:
            return
        for key, value in items.items():
            self[key] = value

    def key_names(self) -> set[str]:
        return set(self._key_by_name.keys())

    def __repr__(self) -> str:
        return f'{type(self).__name__}({repr(self._values)})'

    def __iter__(self) -> Iterator[Property]:
        return iter(self._key_by_name.values())

    def __len__(self) -> int:
        return len(self._values)

    def _get_key(self, key: str | Property) -> Property:
        if isinstance(key, str):
            if key in self._key_by_id:
                return self._key_by_id[key]
            return self._key_by_name[key]
        if isinstance(key, Property):
            # TODO: add frozen key options (if user copied only keys from another properties instance)
            #  this will check `key in self._key_by_name()`
            return key
        raise NotionDfKeyError('bad key', {'key': key})

    def __getitem__(self, key: str | Property) -> PropertyValue_T:
        return self._values[self._get_key(key)]

    def get(self, key: str | Property, default: Optional[PropertyValue_T] = None) -> Optional[PropertyValue_T]:
        try:
            key = self._get_key(key)
            return self[key.name]
        except KeyError:
            return default

    def __setitem__(self, key: str | Property, value: PropertyValue_T) -> None:
        key = self._get_key(key)
        self._key_by_id[key.id] = key
        self._key_by_name[key.name] = key
        self._values[key] = value

    def __delitem__(self, key: str | Property) -> None:
        # TODO restore KeyError
        key = self._get_key(key)
        self._key_by_name.pop(key.name, None)
        self._key_by_id.pop(key.id, None)
        del self._values[key]


class DatabaseProperties(Properties,
                         MutableMapping[Property[DatabasePropertyValue_T, Any, Any], DatabasePropertyValue_T]):
    def __init__(
            self, properties: Optional[dict[
                Property[DatabasePropertyValue_T, Any, Any], DatabasePropertyValue_T]] = None):
        super().__init__(properties)

    def serialize(self) -> dict[str, Any]:
        return {key.name: {
            'type': key.typename,
            key.typename: serialize(value),
        } for key, value in self.items()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in serialized.items():
            typename = prop_serialized['type']
            property_key_cls = property_registry[typename]
            property_key = property_key_cls(prop_name)
            property_key.id = prop_serialized['id']
            # noinspection PyProtectedMember
            property_value = property_key_cls._deserialize_database(prop_serialized)
            self[property_key] = property_value
        return self

    def __getitem__(self, key: str | Property[DatabasePropertyValue_T, Any, Any]) -> DatabasePropertyValue_T:
        return super().__getitem__(key)

    def __setitem__(self, key: str | Property[DatabasePropertyValue_T, Any, Any],
                    value: DatabasePropertyValue_T) -> None:
        return super().__setitem__(key, value)

    def __delitem__(self, key: str | Property[DatabasePropertyValue_T, Any, Any]) -> None:
        return super().__delitem__(key)


class PageProperties(Properties, MutableMapping[Property[Any, PagePropertyValue_T, Any], PagePropertyValue_T]):
    def __init__(
            self, properties: Optional[dict[Property[Any, PagePropertyValue_T, Any], PagePropertyValue_T]] = None):
        super().__init__(properties)
        self._title: Optional[TitleProperty] = None

    def __getitem__(self, key: str | Property[Any, PagePropertyValue_T, Any]) \
            -> PagePropertyValue_T:
        return super().__getitem__(key)

    def __setitem__(self, key: str | Property[Any, PagePropertyValue_T, Any],
                    value: PagePropertyValue_T) -> None:
        return super().__setitem__(key, value)

    def __delitem__(self, key: str | Property[Any, PagePropertyValue_T, Any]) \
            -> None:
        return super().__delitem__(key)

    def serialize(self) -> dict[str, Any]:
        # noinspection PyProtectedMember
        return {key.name: {
            'type': key.typename,
            key.typename: key._serialize_page(value),
        } for key, value in self.items()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in serialized.items():
            typename = prop_serialized['type']
            property_key_cls = property_registry[typename]
            property_key = property_key_cls(prop_name)
            property_key.id = prop_serialized['id']
            # noinspection PyProtectedMember
            property_value = property_key_cls._deserialize_page(prop_serialized)
            self[property_key] = property_value

            if isinstance(property_key, TitleProperty):
                self._title = property_key
        return self

    @property
    def title(self) -> TitleProperty.page_value:
        # TODO
        if self._title is None:
            raise NotionDfKeyError('title key is missing')
        return self[self._title]

    @title.setter
    def title(self, value: TitleProperty.page_value) -> None:
        if self._title is None:
            raise NotionDfKeyError('title key is missing')
        self[self._title] = value


class DatabasePropertyValue(DualSerializable, metaclass=ABCMeta):
    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


@dataclass
class PlainDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ["title", "rich_text", "date", "people", "files", "checkbox", "url",
    "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]"""


@dataclass
class NumberDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['number']"""
    format: NumberFormat


@dataclass
class SelectDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['select', 'multi_select']"""
    options: list[SelectOption]


@dataclass
class StatusDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['status']"""
    options: list[SelectOption]
    groups: list[StatusGroups]


@dataclass
class FormulaDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['formula']"""
    expression: str = field()
    r"""example value: 'if(prop(\"In stock\"), 0, prop(\"Price\"))'"""


@dataclass
class RelationDatabasePropertyValue(DatabasePropertyValue, metaclass=ABCMeta):
    """eligible property types: ['relation']"""
    # Note: this class cannot be defined dataclass,
    #  because dataclass does not immediately resolve type hints, which later leads get_type_hints() to fail
    database: Database

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != RelationDatabasePropertyValue:
            return cls._deserialize_this(serialized)
        match (relation_type := serialized['type']):
            case 'single_property':
                subclass = SingleRelationDatabasePropertyValue
            case 'dual_property':
                subclass = DualRelationDatabasePropertyValue
            case _:
                raise NotionDfValueError('invalid relation_type',
                                         {'relation_type': relation_type, 'serialized': serialized})
        return subclass.deserialize(serialized)

    @classmethod
    @cache
    def _get_type_hints(cls) -> dict[str, type]:  # TODO deduplicate
        from notion_df.entity import Database
        return get_type_hints(cls, {**globals(), **{cls.__name__: cls for cls in (Database,)}})


class SingleRelationDatabasePropertyValue(RelationDatabasePropertyValue):
    def serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database.id,
            'type': 'single_property',
            'single_property': {}
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        from notion_df.entity import Database

        return cls(Database(serialized['database_id']))


@dataclass
class DualRelationDatabasePropertyValue(RelationDatabasePropertyValue):
    synced_property: DualRelationProperty

    def serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database.id,
            'type': 'dual_property',
            'dual_property': {'synced_property_name': self.synced_property.name,
                              'synced_property_id': self.synced_property.id}
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        from notion_df.entity import Database

        synced_property = DualRelationProperty(serialized['dual_property']['synced_property_name'])
        synced_property.id = serialized['dual_property']['synced_property_id']

        return cls(database=Database(serialized['database_id']), synced_property=synced_property)


RelationDatabasePropertyValue_T = TypeVar('RelationDatabasePropertyValue_T', bound=RelationDatabasePropertyValue)


@dataclass
class RollupDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['rollup']"""

    function: RollupFunction
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str


class RelationPagePropertyValue(list['Page'], DualSerializable):
    has_more: Optional[bool]  # set by Property._deserialize_page()

    def __init__(self, pages: Iterable[Page] = ()):
        super().__init__(pages)
        self.has_more = None

    def serialize(self) -> Any:
        return [{'id': str(page.id)} for page in self]

    @classmethod
    def _deserialize_this(cls, serialized: list[dict[str, Any]]) -> Self:
        from notion_df.entity import Page

        self = cls([Page(partial_page['id']) for partial_page in serialized])
        return self

    def __bool__(self) -> bool:
        return bool(len(self) or self.has_more)

    def __add__(self, other: Iterable[Page]):
        return RelationPagePropertyValue((*self, *other))

    def __repr__(self) -> str:
        return f'{type(self).__name__}({super().__repr__()})'


@dataclass
class RollupPagePropertyValue(DualSerializable):
    # TODO: dynamically link rollup values to basic values (for example, RelationPageProperty, DatePageProperty)
    function: RollupFunction
    value_typename: Literal['array', 'date', 'number', 'incomplete', 'unsupported']
    value: Any

    def serialize(self) -> Any:
        return {'function': self.function,
                'type': self.value_typename,
                self.value_typename: self.value}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        value_typename = serialized['type']
        return cls(function=serialized['function'], value_typename=value_typename, value=serialized[value_typename])


class CheckboxProperty(Property[PlainDatabasePropertyValue, bool, CheckboxFilterBuilder]):
    typename = 'checkbox'
    database_value = PlainDatabasePropertyValue
    page_value = bool
    _filter_cls = CheckboxFilterBuilder


class CreatedByProperty(Property[PlainDatabasePropertyValue, PartialUser, PeopleFilterBuilder]):
    typename = 'created_by'
    database_value = PlainDatabasePropertyValue
    page_value = PartialUser
    _filter_cls = PeopleFilterBuilder


class CreatedTimeProperty(Property[PlainDatabasePropertyValue, datetime, DateFilterBuilder]):
    typename = 'created_time'
    database_value = PlainDatabasePropertyValue
    page_value = datetime
    _filter_cls = DateFilterBuilder


class DateProperty(Property[PlainDatabasePropertyValue, DateRange, DateFilterBuilder]):
    typename = 'date'
    database_value = PlainDatabasePropertyValue
    page_value = DateRange
    _filter_cls = DateFilterBuilder


class EmailProperty(Property[PlainDatabasePropertyValue, str, TextFilterBuilder]):
    typename = 'email'
    database_value = PlainDatabasePropertyValue
    page_value = str
    _filter_cls = TextFilterBuilder


class FilesProperty(Property[PlainDatabasePropertyValue, Files, FilesFilterBuilder]):
    typename = 'files'
    database_value = PlainDatabasePropertyValue
    page_value = Files
    _filter_cls = FilesFilterBuilder


class FormulaProperty(Property[FormulaDatabasePropertyValue, PagePropertyValue_T, FilterBuilder_T]):
    """cannot access page properties - use subclasses instead."""
    typename = 'formula'
    value_typename: ClassVar[str]
    database_value = FormulaDatabasePropertyValue
    page_value = Any

    @property
    def filter(self) -> FilterBuilder_T:
        def build(filter_condition: dict[str, Any]):
            return FormulaPropertyFilter(self.name, self.typename, self._filter_cls.get_typename(), filter_condition)

        return self._filter_cls(build)

    def _serialize_page(self, prop_value: PropertyValue_T) -> dict[str, Any]:
        return {'type': self.value_typename,
                self.value_typename: prop_value}

    @classmethod
    def _deserialize_page(cls, prop_serialized: dict[str, Any]) -> PropertyValue_T:
        typename = prop_serialized['type']
        value_typename = prop_serialized[typename]['type']
        if cls == FormulaProperty:
            match value_typename:
                case 'boolean':
                    subclass = CheckboxFormulaProperty
                case 'date':
                    subclass = DateFormulaPropertyKey
                case 'number':
                    subclass = NumberFormulaPropertyKey
                case 'string':
                    subclass = StringFormulaPropertyKey
                case _:
                    raise NotionDfValueError('invalid value_typename.',
                                             {'prop_serialized': prop_serialized, 'value_typename': value_typename})
            return subclass._deserialize_page(prop_serialized)
        return deserialize(cls.page_value, prop_serialized[typename][value_typename])


class CheckboxFormulaProperty(FormulaProperty[bool, CheckboxFilterBuilder]):
    value_typename = 'boolean'
    page_value = bool
    _filter_cls = CheckboxFilterBuilder


class DateFormulaPropertyKey(FormulaProperty[Union[date, datetime], DateFilterBuilder]):
    value_typename = 'date'
    page_value = Union[date, datetime, DateRange]
    _filter_cls = DateFilterBuilder


class NumberFormulaPropertyKey(FormulaProperty[Number, NumberFilterBuilder]):
    value_typename = 'number'
    page_value = Number
    _filter_cls = NumberFilterBuilder


class StringFormulaPropertyKey(FormulaProperty[str, TextFilterBuilder]):
    value_typename = 'string'
    page_value = str
    _filter_cls = TextFilterBuilder


class LastEditedByProperty(Property[PlainDatabasePropertyValue, PartialUser, PeopleFilterBuilder]):
    typename = 'last_edited_by'
    database_value = PlainDatabasePropertyValue
    page_value = PartialUser
    _filter_cls = PeopleFilterBuilder


class LastEditedTimeProperty(Property[PlainDatabasePropertyValue, datetime, DateFilterBuilder]):
    typename = 'last_edited_time'
    database_value = PlainDatabasePropertyValue
    page_value = datetime
    _filter_cls = DateFilterBuilder


class MultiSelectProperty(Property[SelectDatabasePropertyValue, list[SelectOption], MultiSelectFilterBuilder]):
    typename = 'multi_select'
    database_value = SelectDatabasePropertyValue
    page_value = list[SelectOption]
    _filter_cls = MultiSelectFilterBuilder


class NumberProperty(Property[NumberDatabasePropertyValue, Number, NumberFilterBuilder]):
    typename = 'number'
    database_value = NumberDatabasePropertyValue
    page_value = Number
    _filter_cls = NumberFilterBuilder


class PeopleProperty(Property[PlainDatabasePropertyValue, list[User], PeopleFilterBuilder]):
    typename = 'people'
    database_value = PlainDatabasePropertyValue
    page_value = list[User]
    _filter_cls = PeopleFilterBuilder


class PhoneNumberProperty(Property[PlainDatabasePropertyValue, str, TextFilterBuilder]):
    typename = 'phone_number'
    database_value = PlainDatabasePropertyValue
    page_value = str
    _filter_cls = TextFilterBuilder


class RelationProperty(Property[RelationDatabasePropertyValue_T, RelationPagePropertyValue, RelationFilterBuilder]):
    """cannot access database properties - use subclasses instead."""
    typename = 'relation'
    database_value: type[RelationDatabasePropertyValue] = RelationDatabasePropertyValue
    page_value = RelationPagePropertyValue
    _filter_cls = RelationFilterBuilder

    @classmethod
    def _deserialize_page(cls, prop_serialized: dict[str, Any]) -> PropertyValue_T:
        prop_value = super()._deserialize_page(prop_serialized)
        prop_value.has_more = prop_serialized['has_more']
        return prop_value


class SingleRelationProperty(RelationProperty[SingleRelationDatabasePropertyValue]):
    database_value = SingleRelationDatabasePropertyValue


class DualRelationProperty(RelationProperty[DualRelationDatabasePropertyValue]):
    database_value = DualRelationDatabasePropertyValue


class RollupProperty(Property[RollupDatabasePropertyValue, RollupPagePropertyValue, Any]):
    typename = 'rollup'
    database_value = RollupDatabasePropertyValue
    page_value = RollupPagePropertyValue  # TODO
    _filter_cls = Any  # TODO


class RichTextProperty(Property[PlainDatabasePropertyValue, RichText, TextFilterBuilder]):
    typename = 'rich_text'
    database_value = PlainDatabasePropertyValue
    page_value = RichText
    _filter_cls = TextFilterBuilder


class TitleProperty(Property[PlainDatabasePropertyValue, RichText, TextFilterBuilder]):
    typename = 'title'
    database_value = PlainDatabasePropertyValue
    page_value = RichText
    _filter_cls = TextFilterBuilder


class SelectProperty(Property[SelectDatabasePropertyValue, SelectOption, SelectFilterBuilder]):
    typename = 'select'
    database_value = SelectDatabasePropertyValue
    page_value = SelectOption
    _filter_cls = SelectFilterBuilder


class StatusProperty(Property[StatusDatabasePropertyValue, SelectOption, SelectFilterBuilder]):
    typename = 'status'
    database_value = StatusDatabasePropertyValue
    page_value = SelectOption
    _filter_cls = SelectFilterBuilder


class URLProperty(Property[PlainDatabasePropertyValue, str, TextFilterBuilder]):
    typename = 'url'
    database_value = PlainDatabasePropertyValue
    page_value = str
    _filter_cls = TextFilterBuilder

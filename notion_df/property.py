from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from dataclasses import dataclass, field
from datetime import datetime, date
from functools import cache
from typing import (
    ClassVar,
    TypeVar,
    Generic,
    Any,
    Iterator,
    Optional,
    Literal,
    Union,
    Iterable,
    Final,
    get_type_hints,
    cast,
    overload,
)

from typing_extensions import Self

from notion_df.constant import RollupFunction, NumberFormat, Number
from notion_df.core.collection import FinalDict
from notion_df.core.exception import ImplementationError
from notion_df.core.serialization import DualSerializable, deserialize, serialize
from notion_df.core.struct import repr_object
from notion_df.entity import Page, Database
from notion_df.file import Files
from notion_df.filter import (
    PropertyFilter,
    CheckboxFilterBuilder,
    PeopleFilterBuilder,
    DateFilterBuilder,
    TextFilterBuilder,
    FilesFilterBuilder,
    NumberFilterBuilder,
    MultiSelectFilterBuilder,
    RelationFilterBuilder,
    SelectFilterBuilder,
    FilterBuilder,
    FormulaPropertyFilter,
)
from notion_df.misc import StatusGroups, SelectOption, DateRange
from notion_df.rich_text import RichText
from notion_df.user import PartialUser, User

property_registry: FinalDict[str, type[Property]] = FinalDict()
PVT = TypeVar("PVT")
"""PropertyValueT"""
# TODO (low priority): fix that `DPVT.bound == DatabasePropertyValue` does not ruin the type hinting
DPVT = TypeVar("DPVT")
"""DatabasePropertyValueT"""
PPVT = TypeVar("PPVT")
"""PagePropertyValueT"""
FBT = TypeVar("FBT", bound=FilterBuilder)
"""FilterBuilderType"""


# TODO: PropertyMeta
#  - __repr__(typ: PropertyMeta): return(cls_attributes)
#  - cls_attributes
#    - use_dataclass: bool = (inherit)
#
# TODO: UnsupportedProperty by default
#
# TODO resolve following typing error:
#   class Datei(TitleIndexedPage):
#       title_prop = TitleProperty("제목")
#   Datei.title_prop.foo()  # Datei.title_prop is recognized as None in PyCharm
class Property(Generic[DPVT, PPVT, FBT], metaclass=ABCMeta):
    # TODO: move base class and PropertyValue classes to notion_df.core.property
    typename: ClassVar[str] = ""
    database_value: type[DPVT]
    page_value: type[PPVT]
    _filter_cls: type[FBT]

    def __init__(self, name: Optional[str]):
        # TODO: consider signature `(self, *, name: Optional[str], id: Optional[str])`
        #  - raise ValueError if both are empty
        self.name: Final[str] = name
        self.id: Optional[str] = None

    def __repr__(self) -> str:
        return repr_object(self, name=self.name, id=self.id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Property):
            return False
        if all([self.name, other.name]) and self.name != other.name:
            return False
        if all([self.id, other.id]) and self.id != other.id:
            return False
        if not (
            issubclass(type(self), type(other)) or issubclass(type(other), type(self))
        ):
            return False
        return True

    def __hash__(self):
        # TODO: make Properties able to resolve elements(__getitem__, __setitem__, __delitem__)
        #  both using self.name and self.id
        return hash(self.name)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return
        assert cls.typename
        if cls.typename != cast(cls, super(cls, cls)).typename:
            property_registry[cls.typename] = cls

    @property
    def filter(self) -> FBT:
        def build(filter_condition: dict[str, Any]):
            return PropertyFilter(self.name, self.typename, filter_condition)

        return self._filter_cls(build)

    # TODO
    #  - integrate inside PageProperties - _serialize_page(), _deserialize_page(), _deserialize_database()
    #   since we will not create Property types dynamically
    #  - rewrite to _deserialize_page_item(), return tuple[Prop, PropValue]
    #  - RetrievePagePropertyItem.execute() & Page.retrieve_property_item() should call this and return tuple

    # noinspection PyMethodMayBeStatic
    def _serialize_page_value(self, prop_value: PPVT) -> dict[str, Any]:
        # if type(prop_value) != self.page_value:
        #    prop_value = self.page_value(prop_value)
        return serialize(prop_value)

    @classmethod
    def _deserialize_page_value(cls, prop_serialized: dict[str, Any]) -> PPVT:
        """allow proxy-deserialization of subclasses."""
        typename = prop_serialized["type"]
        if cls == Property:
            subclass = property_registry[typename]
            return subclass._deserialize_page_value(prop_serialized)
        return deserialize(cls.page_value, prop_serialized[typename])

    @classmethod
    def _deserialize_database_value(cls, prop_serialized: dict[str, Any]) -> DPVT:
        """allow proxy-deserialization of subclasses."""
        typename = prop_serialized["type"]
        if cls == Property:
            subclass = property_registry[typename]
            return subclass._deserialize_page_value(prop_serialized)
        return deserialize(cls.database_value, prop_serialized[typename])

    def __get__(self, instance, owner):
        # TODO !!! : implement
        #  it should be overridden on all subclasses with no function changes
        #  because of pycharm type inference does not work with TypeVar
        ...


class Properties(DualSerializable, MutableMapping[Property, PVT], metaclass=ABCMeta):
    _prop_by_id: dict[str, Property]
    _prop_by_name: dict[str, Property]
    _prop_value_by_name: dict[str, PVT]
    _prop_value_by_prop: dict[Property, PVT]

    def __init__(self, items: Optional[dict[Property, PVT]] = None):
        self._prop_by_id = {}
        self._prop_by_name = {}
        self._prop_value_by_name = {}
        self._prop_value_by_prop = {}
        if not items:
            return
        for key, value in items.items():
            self[key] = value

    def prop_names(self) -> set[str]:
        return set(self._prop_by_name.keys())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self._prop_value_by_prop)})"

    def __iter__(self) -> Iterator[Property]:
        return iter(self._prop_by_name.values())

    def __len__(self) -> int:
        return len(self._prop_value_by_prop)

    def _get_prop(self, key: str | Property) -> Property:
        if isinstance(key, str):
            if key in self._prop_by_id:
                return self._prop_by_id[key]
            return self._prop_by_name[key]
        if isinstance(key, Property):
            # TODO: make Properties able to resolve elements(__getitem__, __setitem__, __delitem__)
            #  both using self.name and self.id [also see Property.__hash__]
            if key.name is None and (key_by_id := self._prop_by_id.get(key.id)):
                return key_by_id
            # TODO: add frozen key options (if user copied only keys from another properties instance)
            #  this will check `key in self._prop_by_name()`
            return key
        raise KeyError(f"property key not found, {key=}")

    def __getitem__(self, prop: str | Property) -> PVT:
        return self._prop_value_by_prop[self._get_prop(prop)]

    def get(self, prop: str | Property, default: Optional[PVT] = None) -> Optional[PVT]:
        try:
            prop = self._get_prop(prop)
            return self[prop.name]
        except KeyError:
            return default

    def __setitem__(self, prop: str | Property, value: PVT) -> None:
        prop = self._get_prop(prop)
        self._prop_by_id[prop.id] = prop
        self._prop_by_name[prop.name] = prop
        self._prop_value_by_prop[prop] = value

    def __delitem__(self, prop: str | Property) -> None:
        # TODO restore KeyError
        prop = self._get_prop(prop)
        self._prop_by_name.pop(prop.name, None)
        self._prop_by_id.pop(prop.id, None)
        del self._prop_value_by_prop[prop]


class DatabaseProperties(Properties, MutableMapping[Property[DPVT, Any, Any], DPVT]):
    def serialize(self) -> dict[str, Any]:
        return {
            prop.name: {
                "type": prop.typename,
                prop.typename: serialize(prop_value),
            }
            for prop, prop_value in self.items()
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in raw.items():
            typename = prop_serialized["type"]
            prop_cls = property_registry[typename]
            prop = prop_cls(prop_name)
            prop.id = prop_serialized["id"]
            # noinspection PyProtectedMember
            prop_value = prop_cls._deserialize_database_value(prop_serialized)
            self[prop] = prop_value
        return self

    def __getitem__(self, prop: str | Property[DPVT, Any, Any]) -> DPVT:
        return super().__getitem__(prop)

    def __setitem__(self, prop: str | Property[DPVT, Any, Any], value: DPVT) -> None:
        return super().__setitem__(prop, value)

    def __delitem__(self, prop: str | Property[DPVT, Any, Any]) -> None:
        return super().__delitem__(prop)


class PageProperties(Properties, MutableMapping[Property[Any, PPVT, Any], PPVT]):
    def __init__(self, properties: Optional[dict[Property, PPVT]] = None):
        super().__init__(properties)
        self._title_prop: Optional[TitleProperty] = None

    def serialize(self) -> dict[str, Any]:
        # noinspection PyProtectedMember
        return {
            prop.name: {
                "type": prop.typename,
                prop.typename: prop._serialize_page_value(prop_value),
            }
            for prop, prop_value in self.items()
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in raw.items():
            typename = prop_serialized["type"]
            prop_cls = property_registry[typename]
            prop = prop_cls(prop_name)
            prop.id = prop_serialized["id"]
            # noinspection PyProtectedMember
            property_value = prop_cls._deserialize_page_value(prop_serialized)
            self[prop] = property_value

            if isinstance(prop, TitleProperty):
                self._title_prop = prop
        return self

    def __getitem__(self, prop: str | Property[Any, PPVT, Any]) -> PPVT:
        return super().__getitem__(prop)

    def __setitem__(self, prop: str | Property[Any, PPVT, Any], value: PPVT) -> None:
        return super().__setitem__(prop, value)

    def __delitem__(self, prop: str | Property[Any, PPVT, Any]) -> None:
        return super().__delitem__(prop)

    @property
    def title_prop(self) -> TitleProperty | None:
        return self._title_prop

    @property
    def title(self) -> RichText | None:
        return self.get(self.title_prop)

    @title.setter
    def title(self, value: RichText) -> None:
        # TODO raise error if title_prop = None
        self[self.title_prop] = value


class DatabasePropertyValue(DualSerializable, metaclass=ABCMeta):
    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw)


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

    database: Database

    @classmethod
    @abstractmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        raise NotImplementedError

    @classmethod
    def _deserialize_subclass(cls, raw: dict[str, Any]) -> Self:
        match relation_type := raw["type"]:
            case "single_property":
                subclass = SingleRelationDatabasePropertyValue
            case "dual_property":
                subclass = DualRelationDatabasePropertyValue
            case _:
                raise ImplementationError(
                    "invalid relation_type",
                    {"relation_type": relation_type, "serialized": raw},
                )
        return subclass.deserialize(raw)

    @classmethod
    @cache
    def _get_type_hints(cls) -> dict[str, type]:
        return get_type_hints(
            cls, {**globals(), **{cls.__name__: cls for cls in (Database,)}}
        )


class SingleRelationDatabasePropertyValue(RelationDatabasePropertyValue):
    def serialize(self) -> dict[str, Any]:
        return {
            "database_id": self.database.id,
            "type": "single_property",
            "single_property": {},
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(Database(raw["database_id"]))


@dataclass
class DualRelationDatabasePropertyValue(RelationDatabasePropertyValue):
    synced_property: DualRelationProperty

    def serialize(self) -> dict[str, Any]:
        self.synced_property: DualRelationProperty
        return {
            "database_id": self.database.id,
            "type": "dual_property",
            "dual_property": {
                "synced_property_name": self.synced_property.name,
                "synced_property_id": self.synced_property.id,
            },
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        synced_property = DualRelationProperty(
            raw["dual_property"]["synced_property_name"]
        )
        synced_property.id = raw["dual_property"]["synced_property_id"]

        return cls(
            database=Database(raw["database_id"]), synced_property=synced_property
        )


RelationDPVT = TypeVar("RelationDPVT", bound=RelationDatabasePropertyValue)


@dataclass
class RollupDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['rollup']"""

    function: RollupFunction
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str


class RelationPagePropertyValue(MutableSequence["Page"], DualSerializable):
    has_more: Optional[bool]
    """set by Property._deserialize_page().
    if has_more is True, its boolean value is True even if there are no elements on the local object."""

    def __init__(self, pages: Iterable[Page] = ()):
        # TODO: implement OrderedSet and use it (for the sake of Single responsibility principle)
        self._data_list = []
        self._data_set = set()
        self.extend(pages)
        self.has_more = None

    def serialize(self) -> Any:
        return [{"id": str(page.id)} for page in self._data_list]

    @classmethod
    def _deserialize_this(cls, raw: list[dict[str, Any]]) -> Self:
        self = cls([Page(partial_page["id"]) for partial_page in raw])
        return self

    def __repr__(self) -> str:
        return repr_object(self, self._data_list)

    def __len__(self) -> int:
        return len(self._data_list)

    def __contains__(self, page: "Page") -> bool:
        return page in self._data_set

    def __bool__(self) -> bool:
        return bool(len(self) or self.has_more)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, RelationPagePropertyValue)
            and self._data_list == other._data_list
        )

    def __add__(self, other: Iterable[Page]) -> RelationPagePropertyValue:
        return RelationPagePropertyValue((*self, *other))

    def __sub__(self, other: Iterable[Page]) -> RelationPagePropertyValue:
        other_set = set(other)
        return RelationPagePropertyValue(page for page in self if page not in other_set)

    @overload
    @abstractmethod
    def __getitem__(self, index: int) -> "Page": ...

    @overload
    @abstractmethod
    def __getitem__(self, index: slice) -> list["Page"]: ...

    def __getitem__(self, index: int | slice) -> "Page" | list["Page"]:
        return self._data_list[index]

    @overload
    @abstractmethod
    def __setitem__(self, index: int, page: "Page") -> None: ...

    @overload
    @abstractmethod
    def __setitem__(self, index: slice, pages: Iterable["Page"]) -> None: ...

    def __setitem__(
        self, index: int | slice, value: Union["Page", Iterable["Page"]]
    ) -> None:
        if isinstance(index, int) and isinstance(page := value, Page):
            self._data_set.remove(self._data_list[index])
            self._data_set.add(page)
        elif isinstance(index, slice) and isinstance(pages := value, Iterable):
            self._data_set.difference_update(self._data_list[index])
            self._data_set.update(pages)
        else:
            raise TypeError(f"index: {index}, value: {value}")
        self._data_list[index] = value

    @overload
    @abstractmethod
    def __delitem__(self, index: int) -> None: ...

    @overload
    @abstractmethod
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index: int | slice) -> None:
        if isinstance(index, int):
            self._data_set.remove(self._data_list[index])
        elif isinstance(index, slice):
            self._data_set.difference_update(self._data_list[index])
        else:
            raise TypeError(index)
        del self._data_list[index]

    def insert(self, index: int, page: "Page") -> None:
        if page in self:
            return
        self._data_list.insert(index, page)
        self._data_set.add(page)


@dataclass
class RollupPagePropertyValue(DualSerializable):
    # TODO: dynamically link rollup values to basic values (for example, RelationPageProperty, DatePageProperty)
    function: RollupFunction
    value_typename: Literal["array", "date", "number", "incomplete", "unsupported"]
    value: Any

    def serialize(self) -> Any:
        return {
            "function": self.function,
            "type": self.value_typename,
            self.value_typename: self.value,
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        value_typename = raw["type"]
        return cls(
            function=raw["function"],
            value_typename=value_typename,
            value=raw[value_typename],
        )


class CheckboxProperty(
    Property[PlainDatabasePropertyValue, bool, CheckboxFilterBuilder]
):
    typename = "checkbox"
    database_value = PlainDatabasePropertyValue
    page_value = bool
    _filter_cls = CheckboxFilterBuilder


class CreatedByProperty(
    Property[PlainDatabasePropertyValue, PartialUser, PeopleFilterBuilder]
):
    typename = "created_by"
    database_value = PlainDatabasePropertyValue
    page_value = PartialUser
    _filter_cls = PeopleFilterBuilder


class CreatedTimeProperty(
    Property[PlainDatabasePropertyValue, datetime, DateFilterBuilder]
):
    typename = "created_time"
    database_value = PlainDatabasePropertyValue
    page_value = datetime
    _filter_cls = DateFilterBuilder


class DateProperty(Property[PlainDatabasePropertyValue, DateRange, DateFilterBuilder]):
    typename = "date"
    database_value = PlainDatabasePropertyValue
    page_value = DateRange
    _filter_cls = DateFilterBuilder


class EmailProperty(Property[PlainDatabasePropertyValue, str, TextFilterBuilder]):
    typename = "email"
    database_value = PlainDatabasePropertyValue
    page_value = str
    _filter_cls = TextFilterBuilder


class FilesProperty(Property[PlainDatabasePropertyValue, Files, FilesFilterBuilder]):
    typename = "files"
    database_value = PlainDatabasePropertyValue
    page_value = Files
    _filter_cls = FilesFilterBuilder


class FormulaProperty(Property[FormulaDatabasePropertyValue, PPVT, FBT]):
    """cannot access page properties - use subclasses instead."""

    typename = "formula"
    value_typename: ClassVar[str]
    database_value = FormulaDatabasePropertyValue
    page_value = Any

    @property
    def filter(self) -> FBT:
        def build(filter_condition: dict[str, Any]):
            return FormulaPropertyFilter(
                self.name,
                self.typename,
                self._filter_cls.get_typename(),
                filter_condition,
            )

        return self._filter_cls(build)

    def _serialize_page_value(self, prop_value: PVT) -> dict[str, Any]:
        return {"type": self.value_typename, self.value_typename: prop_value}

    @classmethod
    def _deserialize_page_value(cls, prop_serialized: dict[str, Any]) -> PVT:
        typename = prop_serialized["type"]
        value_typename = prop_serialized[typename]["type"]
        if cls == FormulaProperty:
            match value_typename:
                case "boolean":
                    subclass = CheckboxFormulaProperty
                case "date":
                    subclass = DateFormulaPropertyKey
                case "number":
                    subclass = NumberFormulaPropertyKey
                case "string":
                    subclass = StringFormulaPropertyKey
                case _:
                    raise ImplementationError(
                        "invalid value_typename.",
                        {
                            "prop_serialized": prop_serialized,
                            "value_typename": value_typename,
                        },
                    )
            return subclass._deserialize_page_value(prop_serialized)
        return deserialize(cls.page_value, prop_serialized[typename][value_typename])


class CheckboxFormulaProperty(FormulaProperty[bool, CheckboxFilterBuilder]):
    value_typename = "boolean"
    page_value = bool
    _filter_cls = CheckboxFilterBuilder


class DateFormulaPropertyKey(FormulaProperty[Union[date, datetime], DateFilterBuilder]):
    value_typename = "date"
    page_value = Union[date, datetime, DateRange]
    _filter_cls = DateFilterBuilder


class NumberFormulaPropertyKey(FormulaProperty[Number, NumberFilterBuilder]):
    value_typename = "number"
    page_value = Number
    _filter_cls = NumberFilterBuilder


class StringFormulaPropertyKey(FormulaProperty[str, TextFilterBuilder]):
    value_typename = "string"
    page_value = str
    _filter_cls = TextFilterBuilder


class LastEditedByProperty(
    Property[PlainDatabasePropertyValue, PartialUser, PeopleFilterBuilder]
):
    typename = "last_edited_by"
    database_value = PlainDatabasePropertyValue
    page_value = PartialUser
    _filter_cls = PeopleFilterBuilder


class LastEditedTimeProperty(
    Property[PlainDatabasePropertyValue, datetime, DateFilterBuilder]
):
    typename = "last_edited_time"
    database_value = PlainDatabasePropertyValue
    page_value = datetime
    _filter_cls = DateFilterBuilder


class MultiSelectProperty(
    Property[SelectDatabasePropertyValue, list[SelectOption], MultiSelectFilterBuilder]
):
    typename = "multi_select"
    database_value = SelectDatabasePropertyValue
    page_value = list[SelectOption]
    _filter_cls = MultiSelectFilterBuilder


class NumberProperty(
    Property[NumberDatabasePropertyValue, Number, NumberFilterBuilder]
):
    typename = "number"
    database_value = NumberDatabasePropertyValue
    page_value = Number
    _filter_cls = NumberFilterBuilder


class PeopleProperty(
    Property[PlainDatabasePropertyValue, list[User], PeopleFilterBuilder]
):
    typename = "people"
    database_value = PlainDatabasePropertyValue
    page_value: type[list[User]] = list[User]
    _filter_cls = PeopleFilterBuilder


class PhoneNumberProperty(Property[PlainDatabasePropertyValue, str, TextFilterBuilder]):
    typename = "phone_number"
    database_value: type[PlainDatabasePropertyValue] = PlainDatabasePropertyValue
    page_value: type[str] = str
    _filter_cls = TextFilterBuilder


class RelationProperty(
    Property[RelationDPVT, RelationPagePropertyValue, RelationFilterBuilder]
):
    """cannot access database properties - use subclasses instead."""

    typename = "relation"
    database_value: type[RelationDatabasePropertyValue] = RelationDatabasePropertyValue
    page_value: type[RelationPagePropertyValue] = RelationPagePropertyValue
    _filter_cls = RelationFilterBuilder

    @classmethod
    def _deserialize_page_value(cls, prop_serialized: dict[str, Any]) -> PVT:
        prop_value = super()._deserialize_page_value(prop_serialized)
        prop_value.has_more = prop_serialized["has_more"]
        return prop_value


class SingleRelationProperty(RelationProperty[SingleRelationDatabasePropertyValue]):
    database_value = SingleRelationDatabasePropertyValue


class DualRelationProperty(RelationProperty[DualRelationDatabasePropertyValue]):
    database_value = DualRelationDatabasePropertyValue


class RollupProperty(
    Property[RollupDatabasePropertyValue, RollupPagePropertyValue, Any]
):
    typename = "rollup"
    database_value = RollupDatabasePropertyValue
    page_value = RollupPagePropertyValue  # TODO
    _filter_cls = Any  # TODO


class RichTextProperty(
    Property[PlainDatabasePropertyValue, RichText, TextFilterBuilder]
):
    typename = "rich_text"
    database_value = PlainDatabasePropertyValue
    page_value = RichText
    _filter_cls = TextFilterBuilder


class TitleProperty(Property[PlainDatabasePropertyValue, RichText, TextFilterBuilder]):
    typename = "title"
    database_value = PlainDatabasePropertyValue
    page_value = RichText
    _filter_cls = TextFilterBuilder


class SelectProperty(
    Property[SelectDatabasePropertyValue, SelectOption, SelectFilterBuilder]
):
    typename = "select"
    database_value = SelectDatabasePropertyValue
    page_value = SelectOption
    _filter_cls = SelectFilterBuilder


class StatusProperty(
    Property[StatusDatabasePropertyValue, SelectOption, SelectFilterBuilder]
):
    typename = "status"
    database_value = StatusDatabasePropertyValue
    page_value = SelectOption
    _filter_cls = SelectFilterBuilder


class URLProperty(Property[PlainDatabasePropertyValue, str, TextFilterBuilder]):
    typename = "url"
    database_value = PlainDatabasePropertyValue
    page_value = str
    _filter_cls = TextFilterBuilder


class ButtonProperty(Property):  # TODO
    typename = "button"
    database_value = None
    page_value = None

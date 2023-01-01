import inspect
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

from notion_df.resource.core import Deserializable, master
from notion_df.resource.filter import FilterBuilder, TextFilterBuilder
from notion_df.resource.misc import SelectOption, StatusGroups, RollupFunction, NumberFormat, UUID
from notion_df.util.misc import NotionDfValueError


@dataclass
class PropertySchema(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-schema-object
    # https://developers.notion.com/reference/update-property-schema-object
    type: ClassVar[str]
    filter_builder: ClassVar[FilterBuilder]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return
        try:
            cls.type, cls.filter_builder
        except AttributeError:
            raise NotionDfValueError("'type' or 'filter' key is missing", {'cls': cls})

    def plain_serialize(self) -> dict[str, Any]:
        return {
            'type': self.type,
            self.type: self._plain_serialize_value()
        }

    @abstractmethod
    def _plain_serialize_value(self) -> dict[str, Any]:
        pass


@dataclass
@master
class Property(PropertySchema, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-object
    name: str
    id: str

    def plain_serialize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            **super().plain_serialize()
        }


@dataclass
class _PlainPropertySchema(PropertySchema):
    def _plain_serialize_value(self) -> dict[str, Any]:
        return {}


@dataclass
class TitlePropertySchema(_PlainPropertySchema):
    type = 'title'
    filter_builder = TextFilterBuilder


@dataclass
class TitleProperty(Property, TitlePropertySchema):
    pass


@dataclass
class TextPropertySchema(_PlainPropertySchema):
    type = 'rich_text'
    filter_builder = TextFilterBuilder


@dataclass
class TextProperty(Property, TextPropertySchema):
    pass


@dataclass
class NumberPropertySchema(PropertySchema):
    type = 'number'
    format: NumberFormat

    def _plain_serialize_value(self) -> dict[str, Any]:
        return {'format': self.format}


@dataclass
class NumberProperty(Property, NumberPropertySchema):
    pass


@dataclass
class SelectPropertySchema(PropertySchema):
    type = 'select'
    options: list[SelectOption]

    def _plain_serialize_value(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class SelectProperty(Property, SelectPropertySchema):
    pass


@dataclass
class StatusPropertySchema(PropertySchema):
    type = 'status'
    options: list[SelectOption]
    groups: list[StatusGroups]

    def _plain_serialize_value(self) -> dict[str, Any]:
        return {
            'options': self.options,
            'groups': self.groups
        }


@dataclass
class StatusProperty(Property, StatusPropertySchema):
    pass


@dataclass
class MultiSelectPropertySchema(PropertySchema):
    type = 'multi_select'
    options: list[SelectOption]

    def _plain_serialize_value(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class MultiSelectProperty(Property, MultiSelectPropertySchema):
    pass


@dataclass
class DatePropertySchema(_PlainPropertySchema):
    type = 'date'


@dataclass
class DateProperty(Property, DatePropertySchema):
    pass


@dataclass
class PeoplePropertySchema(_PlainPropertySchema):
    type = 'people'


@dataclass
class PeopleProperty(Property, PeoplePropertySchema):
    pass


@dataclass
class FilesPropertySchema(_PlainPropertySchema):
    type = 'files'


@dataclass
class FilesProperty(Property, FilesPropertySchema):
    pass


@dataclass
class CheckboxPropertySchema(_PlainPropertySchema):
    type = 'checkbox'


@dataclass
class CheckboxProperty(Property, CheckboxPropertySchema):
    pass


@dataclass
class URLPropertySchema(_PlainPropertySchema):
    type = 'url'
    filter_builder = TextFilterBuilder


@dataclass
class URLProperty(Property, URLPropertySchema):
    pass


@dataclass
class EmailPropertySchema(_PlainPropertySchema):
    type = 'email'
    filter_builder = TextFilterBuilder


@dataclass
class EmailProperty(Property, EmailPropertySchema):
    pass


@dataclass
class PhoneNumberPropertySchema(_PlainPropertySchema):
    type = 'phone_number'
    filter_builder = TextFilterBuilder


@dataclass
class PhoneNumberProperty(Property, PhoneNumberPropertySchema):
    pass


@dataclass
class FormulaPropertySchema(PropertySchema):
    type = 'formula'
    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    def _plain_serialize_value(self) -> dict[str, Any]:
        pass


@dataclass
class FormulaProperty(Property, FormulaPropertySchema):
    pass


@dataclass
class RelationPropertySchema(PropertySchema):
    database_id: UUID

    def _plain_serialize_value(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': self.type,
            self.type: self._plain_serialize_inner_value()
        }

    @abstractmethod
    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        pass


@dataclass
class RelationProperty(Property, RelationPropertySchema, metaclass=ABCMeta):
    pass


@dataclass
class SingleRelationPropertySchema(RelationPropertySchema):
    type = 'single_property'

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {}


@dataclass
class SingleRelationProperty(RelationProperty, SingleRelationPropertySchema):
    pass


@dataclass
class DualRelationPropertySchema(RelationPropertySchema):
    type = 'dual_property'
    synced_property_name: str
    synced_property_id: str

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'synced_property_name': self.synced_property_name,
            'synced_property_id': self.synced_property_id,
        }


@dataclass
class DualRelationProperty(RelationProperty, DualRelationPropertySchema):
    pass


@dataclass
class RollupPropertySchema(PropertySchema):
    type = 'rollup'
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str
    function: RollupFunction

    def _plain_serialize_value(self) -> dict[str, Any]:
        return {
            'relation_property_name': self.relation_property_name,
            'relation_property_id': self.relation_property_id,
            'rollup_property_name': self.rollup_property_name,
            'rollup_property_id': self.rollup_property_id,
            'function': self.function,
        }


@dataclass
class RollupProperty(Property, RollupPropertySchema):
    pass


@dataclass
class CreatedTimePropertySchema(_PlainPropertySchema):
    type = 'created_time'


@dataclass
class CreatedTimeProperty(Property, CreatedTimePropertySchema):
    pass


@dataclass
class CreatedByPropertySchema(_PlainPropertySchema):
    type = 'created_by'


@dataclass
class CreatedByProperty(Property, CreatedByPropertySchema):
    pass


@dataclass
class LastEditedTimePropertySchema(_PlainPropertySchema):
    type = 'last_edited_time'


@dataclass
class LastEditedTimeProperty(Property, LastEditedTimePropertySchema):
    pass


@dataclass
class LastEditedByPropertySchema(_PlainPropertySchema):
    type = 'last_edited_by'


@dataclass
class LastEditedByProperty(Property, LastEditedByPropertySchema):
    pass

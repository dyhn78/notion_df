from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Any

from notion_df.object.common import SelectOptions, SelectOption
from notion_df.object.constant import Number
from notion_df.object.file import Files
from notion_df.object.filter import CheckboxFilterBuilder, PeopleFilterBuilder, DateFilterBuilder, TextFilterBuilder, \
    FilesFilterBuilder, NumberFilterBuilder, MultiSelectFilterBuilder, RelationFilterBuilder, SelectFilterBuilder
from notion_df.object.property import PropertyKey, PlainDatabasePropertyValue, FormulaDatabasePropertyValue, \
    PropertyValue_T, SelectDatabasePropertyValue, NumberDatabasePropertyValue, RelationDatabasePropertyValue, \
    RelationPagePropertyValue, SingleRelationDatabasePropertyValue, DualRelationDatabasePropertyValue, \
    RollupDatabasePropertyValue, RollupPagePropertyValue, StatusDatabasePropertyValue
from notion_df.object.rich_text import RichTexts
from notion_df.object.user import PartialUser, Users


class CheckboxPropertyKey(PropertyKey[CheckboxFilterBuilder]):
    typename = 'checkbox'
    database = PlainDatabasePropertyValue
    page = bool
    _filter_cls = CheckboxFilterBuilder


class CreatedByPropertyKey(PropertyKey[PeopleFilterBuilder]):
    typename = 'created_by'
    database = PlainDatabasePropertyValue
    page = PartialUser
    _filter_cls = PeopleFilterBuilder


class CreatedTimePropertyKey(PropertyKey[DateFilterBuilder]):
    typename = 'created_time'
    database = PlainDatabasePropertyValue
    page = datetime
    _filter_cls = DateFilterBuilder


class DatePropertyKey(PropertyKey[DateFilterBuilder]):
    typename = 'date'
    database = PlainDatabasePropertyValue
    page = datetime
    _filter_cls = DateFilterBuilder


class EmailPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'email'
    database = PlainDatabasePropertyValue
    page = str
    _filter_cls = TextFilterBuilder


class FilesPropertyKey(PropertyKey[FilesFilterBuilder]):
    typename = 'files'
    database = PlainDatabasePropertyValue
    page = Files
    _filter_cls = FilesFilterBuilder


class FormulaPropertyKey(PropertyKey):
    """cannot access page properties - use subclasses instead."""
    typename = 'formula'
    value_typename: ClassVar[str]
    page = None
    database = FormulaDatabasePropertyValue

    def _serialize_page_value(self, prop_value: PropertyValue_T) -> dict[str, Any]:
        return {'type': self.value_typename,
                self.value_typename: prop_value}


class BoolFormulaPropertyKey(FormulaPropertyKey[CheckboxFilterBuilder]):
    value_typename = 'boolean'
    page = bool
    _filter_cls = CheckboxFilterBuilder


class DateFormulaPropertyKey(FormulaPropertyKey[DateFilterBuilder]):
    value_typename = 'date'
    page = datetime
    _filter_cls = DateFilterBuilder


class NumberFormulaPropertyKey(FormulaPropertyKey[NumberFilterBuilder]):
    value_typename = 'number'
    page = Number
    _filter_cls = NumberFilterBuilder


class StringFormulaPropertyKey(FormulaPropertyKey[TextFilterBuilder]):
    value_typename = 'string'
    page = str
    _filter_cls = TextFilterBuilder


class LastEditedByPropertyKey(PropertyKey[PeopleFilterBuilder]):
    typename = 'last_edited_by'
    database = PlainDatabasePropertyValue
    page = PartialUser
    _filter_cls = PeopleFilterBuilder


class LastEditedTimePropertyKey(PropertyKey[DateFilterBuilder]):
    typename = 'last_edited_time'
    database = PlainDatabasePropertyValue
    page = datetime
    _filter_cls = DateFilterBuilder


class MultiSelectPropertyKey(PropertyKey[MultiSelectFilterBuilder]):
    typename = 'multi_select'
    database = SelectDatabasePropertyValue
    page = SelectOptions
    _filter_cls = MultiSelectFilterBuilder


class NumberPropertyKey(PropertyKey[NumberFilterBuilder]):
    typename = 'number'
    database = NumberDatabasePropertyValue
    page = Number
    _filter_cls = NumberFilterBuilder


class PeoplePropertyKey(PropertyKey[PeopleFilterBuilder]):
    typename = 'people'
    database = PlainDatabasePropertyValue
    page = Users
    _filter_cls = PeopleFilterBuilder


class PhoneNumberPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'phone_number'
    database = PlainDatabasePropertyValue
    page = str
    _filter_cls = TextFilterBuilder


class RelationPropertyKey(PropertyKey[RelationFilterBuilder]):
    """cannot access database properties - use subclasses instead."""
    typename = 'relation'
    database = RelationDatabasePropertyValue
    page = RelationPagePropertyValue
    _filter_cls = RelationFilterBuilder

    @classmethod
    def _deserialize_page_value(cls, prop_serialized: dict[str, Any], typename: str) -> PropertyValue_T:
        prop_value = super()._deserialize_page_value(prop_serialized, typename)
        prop_value.has_more = prop_serialized['has_more']
        return prop_value


class SingleRelationPropertyKey(PropertyKey[RelationFilterBuilder]):
    database = SingleRelationDatabasePropertyValue


class DualRelationPropertyKey(PropertyKey[RelationFilterBuilder]):
    database = DualRelationDatabasePropertyValue


class RollupPropertyKey(PropertyKey):
    typename = 'rollup'
    database = RollupDatabasePropertyValue
    page = RollupPagePropertyValue  # TODO
    _filter_cls = None  # TODO


class RichTextPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'rich_text'
    database = PlainDatabasePropertyValue
    page = RichTexts
    _filter_cls = TextFilterBuilder


class TitlePropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'title'
    database = PlainDatabasePropertyValue
    page = RichTexts
    _filter_cls = TextFilterBuilder


class SelectPropertyKey(PropertyKey[SelectFilterBuilder]):
    typename = 'select'
    database = SelectDatabasePropertyValue
    page = SelectOption
    _filter_cls = SelectFilterBuilder


class StatusPropertyKey(PropertyKey[SelectFilterBuilder]):
    typename = 'status'
    database = StatusDatabasePropertyValue
    page = SelectOption
    _filter_cls = SelectFilterBuilder


class URLPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'url'
    database = PlainDatabasePropertyValue
    page = str
    _filter_cls = TextFilterBuilder

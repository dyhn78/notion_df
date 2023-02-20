from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Final, TypeVar, Generic

from notion_df.resource.core import Deserializable, set_master
from notion_df.resource.misc import SelectOption, StatusGroups, RollupFunction, NumberFormat, UUID


@dataclass
class PropertySchema(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-schema-object
    # https://developers.notion.com/reference/update-property-schema-object
    type: ClassVar[str]

    @classmethod
    @abstractmethod
    def _get_type(cls) -> str:
        pass

    @classmethod
    def _init_subclass(cls, **kwargs):
        cls.type = cls._get_type()
        super()._init_subclass(**kwargs)

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'type': self.type,
            self.type: self._plain_serialize_main()
        }

    @abstractmethod
    def _plain_serialize_main(self) -> dict[str, Any]:
        pass


PropertySchema_T = TypeVar('PropertySchema_T', bound=PropertySchema)


@dataclass
@set_master
class PropertySchemaResponse(Deserializable, Generic[PropertySchema_T], metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-object
    schema: PropertySchema_T
    name: str
    id: str

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "schema": self.schema,
        }


@dataclass
class _PlainPropertySchema(PropertySchema, metaclass=ABCMeta):
    def _plain_serialize_main(self) -> dict[str, Any]:
        return {}


@dataclass
class TitlePropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'title'


@dataclass
class TextPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'rich_text'


@dataclass
class NumberPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'number'

    format: NumberFormat

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {'format': self.format}


@dataclass
class SelectPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'select'

    options: list[SelectOption]

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class StatusPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'status'

    options: list[SelectOption]
    groups: list[StatusGroups]

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'options': self.options,
            'groups': self.groups
        }

@dataclass
class MultiSelectPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'multi_select'

    options: list[SelectOption]

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class DatePropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'date'


@dataclass
class PeoplePropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'people'


@dataclass
class FilesPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'files'


@dataclass
class CheckboxPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'checkbox'


@dataclass
class URLPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'url'



@dataclass
class EmailPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'email'



@dataclass
class PhoneNumberPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'phone_number'



@dataclass
class FormulaPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'formula'

    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    def _plain_serialize_main(self) -> dict[str, Any]:
        pass  # TODO


@dataclass
class RelationPropertySchema(PropertySchema):
    database_id: UUID

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': self.type,
            self.type: self._plain_serialize_inner_value()
        }

    @abstractmethod
    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        pass


@dataclass
class SingleRelationPropertySchema(RelationPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'single_property'

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {}


@dataclass
class DualRelationPropertySchema(RelationPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'dual_property'

    synced_property_name: str
    synced_property_id: str

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'synced_property_name': self.synced_property_name,
            'synced_property_id': self.synced_property_id,
        }


@dataclass
class RollupPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'rollup'

    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str
    function: RollupFunction

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'relation_property_name': self.relation_property_name,
            'relation_property_id': self.relation_property_id,
            'rollup_property_name': self.rollup_property_name,
            'rollup_property_id': self.rollup_property_id,
            'function': self.function,
        }


@dataclass
class CreatedTimePropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'created_time'


@dataclass
class CreatedByPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'created_by'


@dataclass
class LastEditedTimePropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'last_edited_time'



@dataclass
class LastEditedByPropertySchema(_PlainPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'last_edited_by'


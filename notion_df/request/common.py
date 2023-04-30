from __future__ import annotations

from typing import TypeVar, Any, Union

from notion_df.object.block import BlockType
from notion_df.object.database import DatabaseProperty
from notion_df.object.page import PageProperty

PropertyType_T = TypeVar('PropertyType_T', bound=type[PageProperty] | type[DatabaseProperty])


def serialize_properties(property_list: list[PropertyType_T]) -> dict[str, Any]:
    return {prop.name: prop for prop in property_list}


def deserialize_properties(response_data: dict[str, Union[Any, dict[str, Any]]],
                           property_type: PropertyType_T) -> dict[str, PropertyType_T]:
    properties = {}
    for prop_name, prop_serialized in response_data['properties'].items():
        prop = property_type.deserialize(prop_serialized)
        prop.name = prop_name
        properties[prop_name] = prop
    return properties


def serialize_partial_block_list(block_type_list: list[BlockType]) -> list[dict[str, Any]]:
    return [{
        "object": "block",
        "type": type_object,
        type_object.get_typename(): type_object,
    } for type_object in block_type_list]

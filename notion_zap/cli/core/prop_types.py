from enum import Enum, auto


class PropertyTypes(Enum):
    text = auto
    rich_text = auto
    title = auto
    # TODO


PARSER_TYPE = {
    # TODO: VALUE_FORMATS
}


# match parser_type to data_types
VALUE_TYPES = {
    'text': ['text', 'rich_text', 'title'],
    'select': ['select'],
    'multi_select': ['multi_select'],
    'person': ['people', 'person', 'created_by', 'last_edited_by'],
    'manual_date': ['date'],
    'auto_date': ['created_time', 'last_edited_time'],
    'formula': ['formula'],
    'relation': ['relation'],
    'rollup': ['rollup']
}
# match a data_type to the parser_type
VALUE_FORMATS = {}
for form, types in VALUE_TYPES.items():
    VALUE_FORMATS.update(**{typ: form for typ in types})

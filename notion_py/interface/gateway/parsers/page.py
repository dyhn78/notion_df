from __future__ import annotations

from inspect import signature
from typing import Union, Any, Callable, Iterator

# find types by parsers
from notion_py.interface import common
from .rich_text import parse_rich_texts

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
# find parsers by type
VALUE_FORMATS = {}
for form, types in VALUE_TYPES.items():
    VALUE_FORMATS.update(**{typ: form for typ in types})


class PageListParser:
    def __init__(self, response: dict):
        self.values = [PageParser.parse_query_frag(page_result)
                       for page_result in response['results']]

    def __iter__(self) -> Iterator[PageParser]:
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)


class PageParser:
    def __init__(self, page_id: str, archived=False):
        self.page_id = page_id
        self.archived = archived
        self.prop_types \
            : dict[str, str] = {}  # {prop_key: prop_type for prop_key in _}
        self.prop_ids \
            : dict[str, str] = {}  # {prop_key: prop_id for prop_key in _}
        self.prop_values \
            : dict[str, Any] = {}  # {prop_key: prop_value for prop_key in _}
        self.prop_rich_values = {}
        self.title = ''
        self.title_key = ''
        self._current_prop_type = ''

    @classmethod
    def parse_retrieve(cls, response: dict):
        self = cls(response['id'], response['archived'])
        for prop_key, rich_property_object in response['properties'].items():
            try:
                self.prop_values[prop_key] = \
                    self.parser_unit(rich_property_object, prop_key)
            except TypeError as type_error:
                print(rich_property_object)
                raise type_error
        return self

    @classmethod
    def parse_create(cls, response: dict):
        return cls.parse_retrieve(response)

    @classmethod
    def parse_query_frag(cls, response_frag: dict):
        return cls.parse_retrieve(response_frag)

    def parser_unit(self, rich_property_object, prop_key: str):
        try:
            self.prop_ids[prop_key] = rich_property_object['id']
        except (KeyError, AttributeError):
            """
            this mainly deals with formulas.
            ex) string-type formulas:
                {'id': 'xx', 'type': 'formula', {'string': 'xxxx'}}
            """
            pass
        prop_type = rich_property_object['type']
        self._current_prop_type = prop_type

        prop_object = rich_property_object[prop_type]
        prop_format = VALUE_FORMATS.get(prop_type, 'DEFAULT')
        parser_name = f'_parse_{prop_format}'

        parser: Union[Callable[[Any], Any], Callable[[Any, str], Any],
                      Callable[[Any, str, str], Any]] \
            = getattr(self, parser_name, lambda x: x)
        sig = signature(parser)
        length = len(sig.parameters)
        args = [prop_object, prop_key, prop_type][:length]
        result = parser(*args)

        self.prop_types[prop_key] = self._current_prop_type
        return result

    def _parse_formula(self, prop_object, prop_key):
        return self.parser_unit(prop_object, prop_key)

    @staticmethod
    def _parse_auto_date(prop_object):
        if type(prop_object) != str:
            raise ValueError
        start = prop_object[:-1]
        return common.DateFormat.from_isoformat(start)

    @staticmethod
    def _parse_manual_date(prop_object):
        if prop_object is None:
            return common.DateFormat()
        return common.DateFormat.from_isoformat(prop_object['start'], prop_object['end'])

    def _parse_text(self, prop_object, prop_key, prop_type):
        plain_text, rich_text = parse_rich_texts(prop_object)
        self.prop_rich_values[prop_key] = rich_text
        if prop_type == 'title':
            self.title = plain_text
            self.title_key = prop_key
            self._current_prop_type = 'title'
        return plain_text

    def _parse_rollup(self, prop_object, prop_key):
        value_type = prop_object['type']

        try:
            rollup_merged = prop_object[value_type]
        except KeyError:
            return None

        try:
            result = [self.parser_unit(rollup_element, prop_key)
                      for rollup_element in rollup_merged]
            return sorted(result)
            # result.sort(key=lambda x: x[sorted(x.keys())[0]])
            # 딕셔너리의 키 목록 중 사전순으로 가장 앞에 오는 것으로써 정렬한다.
        except TypeError:
            return rollup_merged

    @staticmethod
    def _parse_select(prop_object):
        if prop_object is None:
            return None
        return prop_object['name']

    @staticmethod
    def _parse_multi_select(prop_object):
        return sorted([select_object['name'] for select_object in prop_object])

    @staticmethod
    def _parse_relation(prop_object):
        result = [relation_object['id'] for relation_object in prop_object]
        return sorted(result)

    @staticmethod
    def _parse_person(prop_object):
        result = []
        for select_object in prop_object:
            try:
                result = select_object['name']
            except KeyError:
                result = 'bot_' + select_object['id'][0:4]
            result.append(result)
        return sorted(result)

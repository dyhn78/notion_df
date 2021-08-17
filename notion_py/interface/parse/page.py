from typing import Union, Any, Callable
from datetime import datetime as datetimeclass

from .rich_text import parse_rich_texts

# find prop_types by prop_format
prop_types = {
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
# find prop_format by prop_type
prop_formats = {}
for form, prop_types in prop_types.items():
    prop_formats.update(**{typ: form for typ in prop_types})


class PageParser:
    def __init__(self, page_id: str):
        self.page_id = page_id
        self.props = {}
        self.props_rich = {}
        self.title = ''

    @classmethod
    def fetch_retrieve(cls, response):
        self = cls(response['id'])
        for prop_name, rich_property_object in response['properties'].items():
            self.props[prop_name] = self.fetch_unit(rich_property_object, prop_name)
        return self

    @classmethod
    def fetch_query_frag(cls, response_frag):
        return cls.fetch_retrieve(response_frag)

    def fetch_unit(self, rich_property_object, prop_name: str):
        prop_type = rich_property_object['type']
        prop_object = rich_property_object[prop_type]
        prop_format = prop_formats[prop_type]

        parser_name = f'_parse_{prop_format}'
        parser: Union[Callable[[Any], Any], Callable[[Any, str], Any],
                      Callable[[Any, str, str], Any]] \
            = getattr(self, parser_name, __default=lambda x: x)
        try:
            result = parser(prop_object)
        except TypeError:
            try:
                result = parser(prop_object, prop_name)
            except TypeError:
                result = parser(prop_object, prop_name, prop_type)
        # TODO > how to auto-fill arguments?

        return result

    def _parse_formula(self, prop_object, prop_name):
        return self.fetch_unit(prop_object, prop_name)

    def _parse_auto_date(self, prop_object):
        start = prop_object[:-1]
        return {'start': self._parse_datestring(start), 'end': None}

    def _parse_manual_date(self, prop_object):
        if type(prop_object) != dict:
            return None
        # key: 'start', 'end'
        return {key: self._parse_datestring(value)
                for key, value in prop_object.items()}

    def _parse_text(self, prop_object, prop_name, prop_type):
        plain_text, rich_text = parse_rich_texts(prop_object)
        self.props_rich[prop_name] = rich_text
        if prop_type == 'title':
            self.title = plain_text
        return plain_text

    def _parse_rollup(self, prop_object, prop_name):
        value_type = prop_object['type']

        try:
            rollup_merged = prop_object[value_type]
        except KeyError:
            return None

        try:
            result = [self.fetch_unit(rollup_element, prop_name)
                      for rollup_element in rollup_merged]
            return sorted(result)
            # result.sort(key=lambda x: x[sorted(x.keys())[0]])
            # 딕셔너리의 키 목록 중 사전순으로 가장 앞에 오는 것으로써 정렬한다.
        except TypeError:
            return rollup_merged

    @staticmethod
    def _parse_datestring(datestring):
        if type(datestring) != str:
            return None
        return datetimeclass.fromisoformat(datestring)

    @staticmethod
    def _parse_select(prop_object):
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

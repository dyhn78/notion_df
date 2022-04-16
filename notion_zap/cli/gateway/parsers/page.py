from __future__ import annotations

import datetime as dt
import inspect
from typing import Union, Any, Callable, Iterator

from notion_zap.cli.structs import DatePropertyValue
from notion_zap.cli.structs.prop_types import VALUE_FORMATS
from .rich_text import parse_rich_texts
from ...utility import url_to_id


class PageListParser:
    def __init__(self, response: dict):
        self.values = [PageParser.parse_query_resp_frag(page_result)
                       for page_result in response['results']]

    def __iter__(self) -> Iterator[PageParser]:
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)


class PageParser:
    def __init__(
            self, page_id: str, archived: bool,
            created_time: dt.datetime, last_edited_time: dt.datetime,
            icon, cover,
    ):
        self.page_id = url_to_id(page_id)
        self.archived = archived
        self.icon = icon  # TODO
        self.cover = cover  # TODO
        self.created_time = created_time
        self.last_edited_time = last_edited_time

        self.data_types: dict[str, str] = {}  # {key: data_type for key in _}
        self.prop_ids: dict[str, str] = {}  # {key: prop_id for key in _}
        self.values: dict[str, Any] = {}  # {key: prop_value for key in _}
        self.rich_values: dict[str, Any] = {}

        # only valid in PageRow.
        self.pagerow_title = ''
        self.pagerow_title_key = ''
        self._current_data_type = ''

    @classmethod
    def parse_retrieve_resp(cls, response: dict):
        self = cls(
            response['id'],
            response['archived'],
            response['created_time'],
            response['last_edited_time'],
            response['icon'],
            response['cover'],
        )
        for prop_key, rich_property_object in response['properties'].items():
            try:
                self.values[prop_key] = \
                    self.parse_column(rich_property_object, prop_key)
            except TypeError as type_error:
                print(rich_property_object)
                raise type_error
        return self

    @classmethod
    def parse_create_resp(cls, response: dict):
        return cls.parse_retrieve_resp(response)

    @classmethod
    def parse_query_resp_frag(cls, response_frag: dict):
        return cls.parse_retrieve_resp(response_frag)

    def parse_column(self, rich_property_object, prop_key: str):
        try:
            self.prop_ids[prop_key] = rich_property_object['id']
        except (KeyError, AttributeError):
            """
            this mainly deals with formulas.
            ex) string-type formulas:
                {'id': 'xx', 'type': 'formula', {'string': 'xxxx'}}
            """
            pass
        data_type = rich_property_object['type']
        self._current_data_type = data_type

        prop_object = rich_property_object[data_type]
        prop_format = VALUE_FORMATS.get(data_type, 'DEFAULT')
        parser_name = f'_parse_{prop_format}'

        parser: Union[Callable[[Any], Any], Callable[[Any, str], Any],
                      Callable[[Any, str, str], Any]] \
            = getattr(self, parser_name, lambda x: x)
        signature = inspect.signature(parser)
        param_count = len(signature.parameters)

        result = parser(*([prop_object, prop_key, data_type][:param_count]))
        self.data_types[prop_key] = self._current_data_type
        return result

    def _parse_formula(self, prop_object, prop_key):
        return self.parse_column(prop_object, prop_key)

    @staticmethod
    def _parse_auto_date(prop_object):
        if type(prop_object) != str:
            raise ValueError
        start = prop_object[:-1]
        # notion api returns auto-datetime
        #  with timezone of utc WITHOUT explicit timezone info.
        return DatePropertyValue.from_utc_isoformat(start)

    @staticmethod
    def _parse_manual_date(prop_object):
        if prop_object is None:
            return DatePropertyValue()
        return DatePropertyValue.from_isoformat(prop_object['start'], prop_object['end'])

    def _parse_text(self, prop_object, prop_key, data_type):
        plain_text, rich_text = parse_rich_texts(prop_object)
        self.rich_values[prop_key] = rich_text
        if data_type == 'title':
            self.pagerow_title = plain_text
            self.pagerow_title_key = prop_key
            self._current_data_type = 'title'
        return plain_text

    def _parse_rollup(self, prop_object, prop_key):
        value_type = prop_object['type']

        try:
            rollup_merged = prop_object[value_type]
        except KeyError:
            return None

        try:
            result = [self.parse_column(rollup_element, prop_key)
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

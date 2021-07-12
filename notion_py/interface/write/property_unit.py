from abc import ABCMeta
from datetime import datetime as datetimeclass, date as dateclass
from typing import Union

from notion_py.interface.structure import ValueCarrier, ListStash


class PageProperty(ValueCarrier, metaclass=ABCMeta):
    def __init__(self, value_type, prop_name, prop_value):
        super().__init__()
        self._value_type = value_type
        self._prop_name = prop_name
        if prop_value is not None:
            self.prop_value = prop_value

    def apply(self):
        return {self._prop_name: self.wrapped_value()}

    def wrapped_value(self):
        return {'type': self._value_type,
                self._value_type: self.prop_value}

    @classmethod
    def number(cls, prop_name, value):
        return cls('number', prop_name, value)

    @classmethod
    def checkbox(cls, prop_name, value):
        return cls('checkbox', prop_name, value)

    @classmethod
    def select(cls, prop_name, value):
        return cls('select', prop_name, value)

    @classmethod
    def files(cls, prop_name, value):
        return cls('files', prop_name, value)

    @classmethod
    def people(cls, prop_name, value):
        return cls('people', prop_name, value)

    @classmethod
    def multi_select(cls, prop_name, values):
        prop_value = [{'name': value} for value in values]
        return cls('multi_select', prop_name, prop_value)

    @classmethod
    def relation(cls, prop_name, page_ids):
        prop_value = [{'id': page_id} for page_id in page_ids]
        return cls('relation', prop_name, prop_value)

    @classmethod
    def date(cls, prop_name,
             start_date: Union[datetimeclass, dateclass], end_date=None):
        prop_value = cls._date_isoformat(start_date, end_date)
        return cls('date', prop_name, prop_value)

    @staticmethod
    def _date_isoformat(start_date: Union[datetimeclass, dateclass], end_date=None):
        if end_date is not None:
            assert type(end_date) in [datetimeclass, dateclass]
        start_string = start_date.isoformat()
        res = dict(start=start_string)

        if end_date is not None:
            end_string = end_date.isoformat()
            res.update(end=end_string)
        return res


class RichTextProperty(PageProperty, ListStash):
    # TODO : Children을 가질 수 있게 수정하기. (우선순위 보통)
    def __init__(self, value_type, prop_name):
        assert value_type in ['text', 'title', 'rich_text']
        super().__init__(value_type, prop_name, None)

    @classmethod
    def plain_form(cls, value_type, prop_name, text_content):
        self = cls(value_type, prop_name)
        self.write_text(text_content)
        return self

    @property
    def prop_value(self):
        return self._unpack()

    def write_text(self, content, link=None):
        self._subdicts.append(self.__text(content, link))

    def write_equation(self, expression: str):
        self._subdicts.append(self.__equation(expression))

    def mention_page(self, page_id):
        self._subdicts.append(self.__mention_page(page_id, 'page'))

    def mention_database(self, database_id):
        self._subdicts.append(self.__mention_page(database_id, 'database'))

    def mention_user(self, user_id):
        self._subdicts.append(self.__mention_page(user_id, 'user'))

    def mention_date(self, start_date: Union[datetimeclass, dateclass], end_date=None):
        self._subdicts.append(self.__mention_date(start_date, end_date))

    @classmethod
    def _wrap_to_rich_text(cls, prop_type, value):
        return {
            'type': prop_type,
            prop_type: value
        }

    @classmethod
    def __text(cls, content, link=None):
        value = {'content': content}
        if link:
            value[link] = link
        return cls._wrap_to_rich_text('text', value)

    @classmethod
    def __equation(cls, expression: str):
        equation = {'expression': expression},
        return cls._wrap_to_rich_text('equation', equation)

    @classmethod
    def __mention_page(cls, target_id, target_class):
        assert target_class in ["user", "page", "database"]
        mention = {target_class: {'id': target_id},
                   'type': target_class}
        return cls._wrap_to_rich_text('mention', mention)

    @classmethod
    def __mention_date(cls, start_date: Union[datetimeclass, dateclass], end_date=None):
        date = cls._date_isoformat(start_date, end_date)
        mention = {'date': date,
                   'type': 'date'}
        return cls._wrap_to_rich_text('mention', mention)


if __name__ == '__main__':
    pass

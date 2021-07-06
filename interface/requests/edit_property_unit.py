from abc import ABCMeta
from datetime import datetime as datetimeclass, date as dateclass
from typing import Union

from interface.structure.carriers import ValueCarrier, ListStash


class PageProperty(ValueCarrier, metaclass=ABCMeta):
    value_type = 'None'

    def __init__(self, prop_name):
        super().__init__()
        self.prop_name = prop_name
        self.prop_value = None

    def apply(self):
        return {self.prop_name: self.prop_value}

    def _wrap_to_prop(self, value):
        return {'type': self.value_type,
                self.value_type: value}


class SimpleProperty(PageProperty):
    def __init__(self, prop_name, value):
        super().__init__(prop_name)
        self.prop_value = self._wrap_to_prop(value)


class NumberProperty(SimpleProperty):
    value_type = 'number'


class CheckboxProperty(SimpleProperty):
    value_type = 'checkbox'


class SelectProperty(SimpleProperty):
    value_type = 'select'


class FilesProperty(SimpleProperty):
    value_type = 'files'


class PeopleProperty(SimpleProperty):
    value_type = 'people'


class MultiSelectProperty(SimpleProperty):
    value_type = 'multi_select'

    def __init__(self, prop_name, values):
        prop_value = [{'name': value} for value in values]
        super().__init__(prop_name, prop_value)


class RelationProperty(SimpleProperty):
    value_type = 'relation'

    def __init__(self, prop_name, page_ids):
        value = [{'id': page_id} for page_id in page_ids]
        super().__init__(prop_name, value)


class DateProperty(SimpleProperty):
    def __init__(self, prop_name,
                 start_date: Union[datetimeclass, dateclass],
                 end_date=Union[datetimeclass, dateclass, None]):
        start_string = start_date.isoformat()
        value = dict(start=start_string)

        if end_date is not None:
            end_string = end_date.isoformat()
            value.update(end=end_string)

        super().__init__(prop_name, value)


class RichTextProperty(PageProperty, ListStash):
    # TODO : Children을 가질 수 있게 수정하기. (우선순위 보통)
    def __init__(self, prop_name, value_type):
        super().__init__(prop_name)
        self.value_type = value_type

    @property
    def prop_value(self):
        return self._wrap_to_prop(self._unpack())

    def append_text(self, content, link=None):
        self._subdicts.append(self.__text(content, link))

    def append_equation(self, expression: str):
        self._subdicts.append(self.__equation(expression))

    def append_mention_page(self, page_id):
        self._subdicts.append(self.__mention_page(page_id, 'page'))

    def append_mention_database(self, database_id):
        self._subdicts.append(self.__mention_page(database_id, 'database'))

    def append_mention_user(self, user_id):
        self._subdicts.append(self.__mention_page(user_id, 'user'))

    def append_mention_date(self, start_date, end_date=None):
        self._subdicts.append(self.__mention_date(start_date, end_date))

    @classmethod
    def __wrap_prop_type(cls, prop_type, value):
        return {
            'type': prop_type,
            prop_type: value
        }

    @classmethod
    def __text(cls, content, link=None):
        value = {'content': content}
        if link:
            value[link] = link
        return cls.__wrap_prop_type('text', value)

    @classmethod
    def __equation(cls, expression: str):
        equation = {'expression': expression},
        return cls.__wrap_prop_type('equation', equation)

    @classmethod
    def __mention_page(cls, target_id, target_class):
        """
        {'mention': {'page': {'id': 'e15c62be-b9e4-4bb5-9b62-9220804fe93f'},
                     'type': 'page'},
         'type': 'mention'}
        """
        assert target_class in ["user", "page", "database"]
        mention = {
            target_class: {'id': target_id},
            'type': target_class
        }
        return cls.__wrap_prop_type('mention', mention)

    @classmethod
    def __mention_date(cls, start_date, end_date=None):
        """
        :param start_date, end_date: ISO8601 date and time
        """
        date = {'start': start_date,
                'end': end_date}
        mention = {'date': date,
                   'type': 'date'}
        return cls.__wrap_prop_type('mention', mention)


def make_block_type(inner_value, block_type):
    return {
        'object': 'block',
        'type': block_type,
        block_type: inner_value
    }

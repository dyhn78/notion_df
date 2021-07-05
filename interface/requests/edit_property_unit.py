from abc import ABCMeta

from interface.requests.structures import ValueCarrier, PlainCarrier, DictStash, ListStash


class PropertyCarrier(ValueCarrier, metaclass=ABCMeta):
    value_type = 'None'

    def __init__(self, prop_name):
        super().__init__()
        self.prop_name = prop_name

    def apply(self):
        return {
            'type': self.value_type,
            self.value_type: self.stash()
        }


class SingletypeProperty(PropertyCarrier, DictStash):
    def __init__(self, prop_name, prop_value):
        super().__init__(prop_name)
        self.add_to_dictstash(PlainCarrier({self.value_type: prop_value}))


class NumberProperty(SingletypeProperty):
    value_type = 'number'


class CheckboxProperty(SingletypeProperty):
    value_type = 'checkbox'


class SelectProperty(SingletypeProperty):
    value_type = 'select'


class FilesProperty(SingletypeProperty):
    value_type = 'files'


class PeopleProperty(SingletypeProperty):
    value_type = 'people'


class MultitypeProperty(PropertyCarrier, ListStash):
    def __init__(self, prop_name, prop_values):
        super().__init__(prop_name)
        self.subcarriers = [PlainCarrier({self.value_type: prop_value}) for prop_value in prop_values]


class MultiSelectProperty(MultitypeProperty):
    value_type = 'multi_select'


class RelationProperty(MultitypeProperty):
    value_type = 'relation'


class DateProperty(PropertyCarrier, DictStash):
    def __init__(self, prop_name, start_date, end_date):
        super().__init__(prop_name)
        self.add_to_dictstash(SingletypeProperty('start', start_date))
        self.add_to_dictstash(SingletypeProperty('end', end_date))


def make_block_type(inner_value, block_type) -> ValueCarrier:
    res = {
        'object': 'block',
        'type': block_type,
        block_type: inner_value
    }
    return PlainCarrier(res)


class RichTextProperty(PropertyCarrier, ListStash):
    # TODO : Children을 가질 수 있게 수정하기. (우선순위 보통)
    def __init__(self, prop_name, value_type, block_type=None):
        super().__init__(prop_name)
        self.value_type = value_type
        self.block_type = block_type

    def apply(self):
        res = super().apply()
        if self.block_type:
            res = make_block_type(res, self.block_type)
        return res

    def append_text(self, content, link=None):
        self.append_to_liststash(self.__text(content, link))

    def append_equation(self, expression: str):
        self.append_to_liststash(self.__equation(expression))

    def append_mention_page(self, page_id):
        self.append_to_liststash(self.__mention_page(page_id, 'page'))

    def append_mention_database(self, database_id):
        self.append_to_liststash(self.__mention_page(database_id, 'database'))

    def append_mention_user(self, user_id):
        self.append_to_liststash(self.__mention_page(user_id, 'user'))

    def append_mention_date(self, start_date, end_date=None):
        self.append_to_liststash(self.__mention_date(start_date, end_date))

    def appendleft_text(self, content, link=None):
        self.appendleft_to_liststash(self.__text(content, link))

    def appendleft_equation(self, expression: str):
        self.appendleft_to_liststash(self.__equation(expression))

    def appendleft_mention_page(self, page_id):
        self.appendleft_to_liststash(self.__mention_page(page_id, 'page'))

    def appendleft_mention_database(self, database_id):
        self.appendleft_to_liststash(self.__mention_page(database_id, 'database'))

    def appendleft_mention_user(self, user_id):
        self.appendleft_to_liststash(self.__mention_page(user_id, 'user'))

    def appendleft_mention_date(self, start_date, end_date=None):
        self.appendleft_to_liststash(self.__mention_date(start_date, end_date))

    @classmethod
    def __prop_type_wrap(cls, prop_type, value):
        return {
            'type': prop_type,
            prop_type: value
        }

    @classmethod
    def __text(cls, content, link=None):
        value = {'content': content}
        if link:
            value[link] = link
        outer_value = cls.__prop_type_wrap('text', value)
        return PlainCarrier(outer_value)

    @classmethod
    def __equation(cls, expression: str):
        equation = {'expression': expression},
        outer_value = cls.__prop_type_wrap('equation', equation)
        return PlainCarrier(outer_value)

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
        outer_value = cls.__prop_type_wrap('mention', mention)
        return PlainCarrier(outer_value)

    @classmethod
    def __mention_date(cls, start_date, end_date=None):
        """
        :param start_date, end_date: ISO8601 date and time
        """
        date = {
            'start': start_date,
            'end': end_date
        }
        mention = {
            'date': date,
            'type': 'date'
        }
        outer_value = cls.__prop_type_wrap('mention', mention)
        return PlainCarrier(outer_value)

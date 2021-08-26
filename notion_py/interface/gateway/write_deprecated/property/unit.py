from abc import ABCMeta
from datetime import datetime as datetimeclass, date as dateclass
from typing import Union, Optional

from notion_py.interface.struct import ValueCarrier, ListStash


class WritePageProperty(ValueCarrier, metaclass=ABCMeta):
    def __init__(self, value_type, prop_name, prop_value):
        super().__init__()
        self.value_type = value_type
        self.prop_name = prop_name
        if prop_value is not None:
            self.prop_value = prop_value

    def unpack(self):
        return {self.prop_name: self._wrap_to_prop()}

    def _wrap_to_prop(self):
        return {'type': self.value_type,
                self.value_type: self.prop_value}

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


class WriteRichTextProperty(WritePageProperty, ListStash):
    def __init__(self, value_type, prop_name, plain_text_contents: Optional[str] = None):
        super().__init__(value_type, prop_name, None)
        if plain_text_contents is not None:
            self.write_text(plain_text_contents)

    @property
    def prop_value(self):
        res = self._unpack()
        return res

    def write_text(self, contents, link=None):
        self._subdicts.append(self._text(contents, link))

    def write_equation(self, expression: str):
        self._subdicts.append(self._equation(expression))

    def mention_page(self, page_id: str):
        self._subdicts.append(self._mention_page(page_id, 'page'))

    def mention_database(self, database_id: str):
        self._subdicts.append(self._mention_page(database_id, 'database'))

    def mention_user(self, user_id: str):
        self._subdicts.append(self._mention_page(user_id, 'user'))

    def mention_date(self, start_date: Union[datetimeclass, dateclass], end_date=None):
        self._subdicts.append(self._mention_date(start_date, end_date))

    @classmethod
    def _wrap_to_rich_text(cls, prop_type, value):
        return {
            'type': prop_type,
            prop_type: value
        }

    @classmethod
    def _text(cls, content, link=None):
        value = {'content': content}
        if link:
            value[link] = link
        return cls._wrap_to_rich_text('text', value)

    @classmethod
    def _equation(cls, expression: str):
        equation = {'expression': expression},
        return cls._wrap_to_rich_text('equation', equation)

    @classmethod
    def _mention_page(cls, target_id, target_class):
        assert target_class in ["user", "page", "database"]
        mention = {target_class: {'id': target_id},
                   'type': target_class}
        return cls._wrap_to_rich_text('mention', mention)

    @classmethod
    def _mention_date(cls, start_date: Union[datetimeclass, dateclass], end_date=None):
        date = cls._date_isoformat(start_date, end_date)
        mention = {'date': date,
                   'type': 'date'}
        return cls._wrap_to_rich_text('mention', mention)


class WriteTitleProperty(WriteRichTextProperty):
    def __init__(self, prop_name, plain_text_content: Optional[str] = None):
        super().__init__('title', prop_name, plain_text_content)

    def _wrap_to_prop(self):
        return {self.value_type: self.prop_value}


class WriteSimplePageProperty(WritePageProperty):
    def __bool__(self):
        pass

    @classmethod
    def number(cls, prop_name, value):
        return cls('number', prop_name, value)

    @classmethod
    def checkbox(cls, prop_name, value):
        return cls('checkbox', prop_name, value)

    @classmethod
    def files(cls, prop_name, value):
        return cls('files', prop_name, value)

    @classmethod
    def people(cls, prop_name, value):
        return cls('people', prop_name, value)

    @classmethod
    def url(cls, prop_name, value):
        return cls('url', prop_name, value)

    @classmethod
    def email(cls, prop_name, value):
        return cls('email', prop_name, value)

    @classmethod
    def phone_number(cls, prop_name, value):
        return cls('phone_number', prop_name, value)

    @classmethod
    def select(cls, prop_name, value):
        return cls('select', prop_name, {'name': value})

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


if __name__ == '__main__':
    pass

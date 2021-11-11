from abc import ABCMeta

from ..carriers import ValueCarrier
from ...struct import DateValue


class RichTextObjectEncoder(ValueCarrier, metaclass=ABCMeta):
    def __init__(self):
        self._list_stash = []
        self._plain_form = []

    def encode(self):
        return self._list_stash

    def plain_form(self):
        """this ignores anything other than texts:
        for example, mentions of pages, dates or users, math equations, ..."""
        return ''.join(self._plain_form)

    @staticmethod
    def _wrap_unit(prop_type, value):
        return {
            'type': prop_type,
            prop_type: value,
        }

    def write_text(self, contents, link=None):
        value = {'content': contents}
        if link:
            value[link] = link
        self._list_stash.append(self._wrap_unit('text', value))
        self._plain_form.append(contents)

    def write_equation(self, expression: str):
        equation = {'expression': expression},
        self._list_stash.append(self._wrap_unit('equation', equation))

    def _mention_entity(self, target_id, target_class):
        assert target_class in ["user", "page", "database"]
        mention = {target_class: {'id': target_id},
                   'type': target_class}
        return self._wrap_unit('mention', mention)

    def mention_date(self, date_value: DateValue):
        date = date_value.make_isoformat()
        mention = {'type': 'date', 'date': date}
        self._list_stash.append(self._wrap_unit('mention', mention))

    def mention_page(self, page_id: str):
        self._list_stash.append(self._mention_entity(page_id, 'page'))

    def mention_database(self, database_id: str):
        self._list_stash.append(self._mention_entity(database_id, 'database'))

    def mention_user(self, user_id: str):
        self._list_stash.append(self._mention_entity(user_id, 'user'))

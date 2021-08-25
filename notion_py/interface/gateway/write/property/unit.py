from abc import ABCMeta

from notion_py.interface.struct import ValueCarrier, ListStash, DateFormat, make_isoformat


class PropertyUnitWriter(ValueCarrier, metaclass=ABCMeta):
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


class RichTextUnitWriter(PropertyUnitWriter, ListStash):
    def __init__(self, value_type, prop_name):
        super().__init__(value_type, prop_name, None)

    @property
    def prop_value(self):
        res = self._unpack()
        return res

    @staticmethod
    def _wrap_to_rich_text(prop_type, value):
        return {
            'type': prop_type,
            prop_type: value
        }

    def _mention_entity(self, target_id, target_class):
        assert target_class in ["user", "page", "database"]
        mention = {target_class: {'id': target_id},
                   'type': target_class}
        return self._wrap_to_rich_text('mention', mention)

    def write_text(self, contents, link=None):
        value = {'content': contents}
        if link:
            value[link] = link
        self._subdicts.append(self._wrap_to_rich_text('text', value))

    def write_equation(self, expression: str):
        equation = {'expression': expression},
        self._subdicts.append(self._wrap_to_rich_text('equation', equation))

    def mention_date(self, date_value: DateFormat):
        date = make_isoformat(date_value)
        mention = {'type': 'date', 'date': date}
        self._subdicts.append(self._wrap_to_rich_text('mention', mention))

    def mention_page(self, page_id: str):
        self._subdicts.append(self._mention_entity(page_id, 'page'))

    def mention_database(self, database_id: str):
        self._subdicts.append(self._mention_entity(database_id, 'database'))

    def mention_user(self, user_id: str):
        self._subdicts.append(self._mention_entity(user_id, 'user'))


class BasicPageTitleWriter(RichTextUnitWriter):
    def __init__(self, prop_name):
        super().__init__('title', prop_name)

    def _wrap_to_prop(self):
        return {self.value_type: self.prop_value}


class SimpleUnitWriter(PropertyUnitWriter):
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
    def multi_select(cls, prop_name, values: list[str]):
        prop_value = [{'name': value} for value in values]
        return cls('multi_select', prop_name, prop_value)

    @classmethod
    def relation(cls, prop_name, page_ids: list[str]):
        prop_value = [{'id': page_id} for page_id in page_ids]
        return cls('relation', prop_name, prop_value)

    @classmethod
    def date(cls, prop_name, value: DateFormat):
        prop_value = make_isoformat(value)
        return cls('date', prop_name, prop_value)

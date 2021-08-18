from typing import Union

from notion_py.gateway.common.date_format import DateFormat
from notion_py.gateway.write.property.unit import \
    SimpleUnitWriter, RichTextUnitWriter, BasicPageTitleWriter


class TabularPropertyAgent:
    @classmethod
    def rich_title(cls, prop_name: str):
        return RichTextUnitWriter('title', prop_name)

    @classmethod
    def rich_text(cls, prop_name: str):
        return RichTextUnitWriter('rich_text', prop_name)

    @classmethod
    def title(cls, prop_name: str, value: str):
        return cls.rich_title(prop_name).write_text(value)

    @classmethod
    def text(cls, prop_name: str, value: str):
        return cls.rich_text(prop_name).write_text(value)

    @classmethod
    def date(cls, prop_name: str, value: DateFormat):
        return SimpleUnitWriter.date(prop_name, value)

    @classmethod
    def url(cls, prop_name: str, value: str):
        return SimpleUnitWriter.url(prop_name, value)

    @classmethod
    def email(cls, prop_name: str, value: str):
        return SimpleUnitWriter.email(prop_name, value)

    @classmethod
    def phone_number(cls, prop_name: str, value: str):
        return SimpleUnitWriter.phone_number(prop_name, value)

    @classmethod
    def number(cls, prop_name: str, value: Union[int, float]):
        return SimpleUnitWriter.number(prop_name, value)

    @classmethod
    def checkbox(cls, prop_name: str, value: bool):
        return SimpleUnitWriter.checkbox(prop_name, value)

    @classmethod
    def select(cls, prop_name: str, value: str):
        return SimpleUnitWriter.select(prop_name, value)

    @classmethod
    def files(cls, prop_name: str, value: str):
        return SimpleUnitWriter.files(prop_name, value)

    @classmethod
    def people(cls, prop_name: str, value: str):
        return SimpleUnitWriter.people(prop_name, value)

    @classmethod
    def multi_select(cls, prop_name: str, values: list[str]):
        return SimpleUnitWriter.multi_select(prop_name, values)

    @classmethod
    def relation(cls, prop_name: str, page_ids: list[str]):
        return SimpleUnitWriter.relation(prop_name, page_ids)


class BasicPropertyAgent:
    @classmethod
    def rich_title(cls):
        return BasicPageTitleWriter('title')

    @classmethod
    def title(cls, value: str):
        return cls.rich_title().write_text(value)

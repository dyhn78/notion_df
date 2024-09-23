from __future__ import annotations

import datetime as dt
import re
from abc import ABCMeta
from enum import Enum
from typing import Optional, ClassVar, NewType, Iterable, Any
from uuid import UUID

from typing_extensions import Self

from app.emoji_code import EmojiCode
from notion_df.core.entity_core import Entity
from notion_df.core.struct import undefined
from notion_df.core.uuid_parser import get_page_or_database_url
from notion_df.data import DatabaseData
from notion_df.entity import Database, Page, Workspace
from notion_df.misc import Emoji
from notion_df.property import TitleProperty, DateFormulaPropertyKey, RichTextProperty, \
    RelationProperty, \
    DateProperty, CheckboxFormulaProperty, SelectProperty, PageProperties
from notion_df.rich_text import RichText

schedule = "일정"
start = "시작"
progress = "진도"
common = '공통'
elements = '요소'
related = '관계'

_entity_to_enum = {}


class DatabaseEnum(Enum):
    event_db = ('일과', 'c8d46c01d6c941a9bf8df5d115a05f03', EmojiCode.BLUE_CIRCLE)
    journal_db = ('바탕', 'fa7d93f6fbd341f089b185745c834811', EmojiCode.BLUE_HEART)
    idea_db = ('꼭지', '52d387ea0aaa470cb69332708c61b34d', EmojiCode.GREEN_CIRCLE)
    thread_db = ('줄기', 'addc94642ee74825bd31109f4fd1c9ee', EmojiCode.GREEN_HEART)
    stage_db = ('수행', 'e8782fe4e1a34c9d846d57b01a370327', EmojiCode.YELLOW_CIRCLE)
    reading_db = ('읽기', 'c326f77425a0446a8aa309478767c85b', EmojiCode.YELLOW_HEART)
    area_db = ('주제', 'eb2f09a1de41412e8b2357bc04f26e74', EmojiCode.RED_CIRCLE)
    resource_db = ('요점', '2c5411ba6a0f43a0a8aa06295751e37a', EmojiCode.RED_HEART)
    datei_db = ('일간', '961d1ca0a3d24a46b838ba85e710f18d', EmojiCode.PURPLE_CIRCLE)
    weeki_db = ('주간', 'd020b399cf5947a59d11a0b9e0ea45d0', EmojiCode.PURPLE_HEART)

    genai_db = ('#GenAI', '16a93035080d4b93b9e4b3db1b52811d', '', Page("383cfe576d684df3823cb1535bebfaf0"))

    depr_event_db = ('일지', 'c226cffe6cf84ab996bbc384bf26bf1d', EmojiCode.ORANGE_CIRCLE)
    depr_writing_db = ('표현', '069bbebd632f4a6ea3044575a064cf0f', EmojiCode.BLACK_HEART)
    depr_stream_db = ('전개', '9f21ad86079d4caaa7ed9461a7f37288', EmojiCode.RED_HEART)
    depr_subject_db = ('담론', 'eca1ba6d4831459ca8becc283f1f8c4e', EmojiCode.PURPLE_HEART)
    depr_people_db = ('인물', '3c08cdba5a044e9c9b7e31ee8509f506', EmojiCode.BLACK_HEART)
    depr_channel_db = ('채널', '2d3f4ea770854b8e9e30abecd4d31a86', EmojiCode.BLACK_HEART)
    depr_location_db = ('장소', '920e2e10225d450d8bb084697f6d0fc6', EmojiCode.BLACK_HEART)
    depr_theme_db = ('주제 -220222', '5464267393e940a58e3f10db306bf3e4', EmojiCode.BLACK_HEART)

    def __init__(self, title: str, id_or_url: str, prefix: str, *args: Any) -> None:
        self._value_ = self._name_
        self.prefix = prefix
        self.title = title
        if args:
            parent = args[0]
        else:
            parent = Workspace()
        self.entity = Database(id_or_url)
        _entity_to_enum[self.entity] = self
        DatabaseData(
            id=self.entity.id,
            parent=parent,
            created_time=undefined,
            last_edited_time=undefined,
            icon=Emoji(self.prefix),
            cover=undefined,
            url=get_page_or_database_url(id_or_url, 'dyhn'),
            title=RichText.from_plain_text(self.title),
            properties=undefined,
            archived=False,
            is_inline=False,
            preview=True
        ).set_preview()

    @property
    def prefix_title(self) -> str:
        return self.prefix + self.title

    @classmethod
    def from_entity(cls, entity: Entity) -> Optional[DatabaseEnum]:
        return _entity_to_enum.get(entity)


def is_template(page: Page) -> bool:
    database = page.data.parent
    if not database or not isinstance(database, Database):
        return False
    return bool(re.match(f'<{database.data.title.plain_text}>.*', page.data.properties.title.plain_text))


korean_weekday = '월화수목금토일'
DateTitleMatch = NewType("DateTitleMatch", re.Match[str])


def parse_date_title_match(match: Optional[DateTitleMatch]) -> Optional[dt.date]:
    if not match:
        return None
    year, month, day = (int(s) for s in match.groups())
    full_year = (2000 if year < 90 else 1900) + year
    try:
        return dt.date(full_year, month, day)
    except ValueError:
        # In case the date is not valid (like '000229' for non-leap year)
        return None


class TitleIndexedPage(Page, metaclass=ABCMeta):
    db: ClassVar[Database]
    title_prop: ClassVar[TitleProperty]
    pages_by_title_plain_text: ClassVar[dict[str, Self]] = {}

    def __init__(self, id_or_url: UUID | str):
        super().__init__(id_or_url)
        self.pages_by_title_plain_text[self.title.plain_text] = self

    @classmethod
    def get_by_title(cls, title_plain_text: str) -> Optional[Self]:
        if page := cls.pages_by_title_plain_text.get(title_plain_text):
            return page
        plain_page_list = cls.db.query(cls.title_prop.filter.equals(title_plain_text))
        if not plain_page_list:
            return
        page = cls(plain_page_list[0].id)
        return page


class Datei(TitleIndexedPage):
    db = DatabaseEnum.datei_db.entity
    title_prop = TitleProperty(EmojiCode.GREEN_BOOK + '제목')
    date_prop = DateProperty(EmojiCode.CALENDAR + '날짜')
    page_by_date_dict: ClassVar[dict[dt.date, Self]] = {}
    getter_pattern = re.compile(r'(\d{2})(\d{2})(\d{2}).*')

    def __init__(self, id_or_url: UUID | str):
        super().__init__(id_or_url)
        self.page_by_date_dict[self.date] = self

    @property
    def date(self) -> dt.date:
        """some new manually created pages can have empty values.
        You should prevent propagation to other Actions by filling them with top priority."""
        return self.properties[self.date_prop].start

    def get_date_in_title(self) -> dt.date:
        match = self.getter_pattern.match(self.title.plain_text)
        date = parse_date_title_match(match)
        if date is None:
            raise RuntimeError(f"Invalid Datei title. {self=}")
        return date

    @classmethod
    def get_or_create(cls, date: dt.date) -> Datei:
        if page_list := cls.db.query(cls.date_prop.filter.equals(date)):
            return cls(page_list[0].id)
        return cls.create(date)

    @classmethod
    def create(cls, date: dt.date) -> Datei:
        day_name = korean_weekday[date.weekday()] + '요일'
        title_plain_text = f'{date.strftime("%y%m%d")} {day_name}'
        plain_page = cls.db.create_child_page(PageProperties({
            cls.title_prop: cls.title_prop.page_value.from_plain_text(title_plain_text),
            cls.date_prop: cls.date_prop.page_value(start=date)
        }))
        return cls(plain_page.id)


class Weeki(TitleIndexedPage):
    db = DatabaseEnum.weeki_db.entity
    title_prop = TitleProperty(EmojiCode.GREEN_BOOK + '제목')
    date_range_prop = DateProperty(EmojiCode.BIG_CALENDAR + '날짜 범위')

    @property
    def date_start(self) -> dt.date:
        return self.properties[self.date_range_prop].start

    @classmethod
    def get_or_create(cls, date: dt.date) -> Page:
        title_plain_text = cls._get_first_day_of_week(date).strftime("%y/%U")
        return (cls.get_by_title(title_plain_text)
                or cls.create(date))

    @classmethod
    def create(cls, date: dt.date) -> Page:
        title_plain_text = cls._get_first_day_of_week(date).strftime("%y/%U")
        page = cls.db.create_child_page(PageProperties({
            cls.title_prop: cls.title_prop.page_value.from_plain_text(
                title_plain_text),
            cls.date_range_prop: cls.date_range_prop.page_value(
                start=cls._get_first_day_of_week(date),
                end=cls._get_last_day_of_week(date))
        }))
        return page

    @classmethod
    def _get_first_day_of_week(cls, date: dt.date) -> dt.date:
        # returns the first day (sunday) of the week.
        weekday = (date.weekday() + 1) % 7
        return date + dt.timedelta(days=-weekday)

    @classmethod
    def _get_last_day_of_week(cls, date: dt.date) -> dt.date:
        return cls._get_first_day_of_week(date) + dt.timedelta(days=6)


record_datetime_auto_prop = DateFormulaPropertyKey(EmojiCode.TIMER + '일시')
record_timestr_prop = RichTextProperty(EmojiCode.CALENDAR + '일지')
datei_to_weeki_prop = RelationProperty(DatabaseEnum.weeki_db.prefix_title)
datei_date_prop = DateProperty(EmojiCode.CALENDAR + '날짜')
weeki_date_range_prop = DateProperty(EmojiCode.BIG_CALENDAR + '날짜 범위')
event_title_prop = TitleProperty(EmojiCode.ORANGE_BOOK + '제목')
event_to_datei_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
event_to_journal_prop = RelationProperty(DatabaseEnum.journal_db.prefix_title)
event_to_stage_prop = RelationProperty(DatabaseEnum.stage_db.prefix_title)
event_to_reading_prop = RelationProperty(DatabaseEnum.reading_db.prefix_title)
journal_kind_prop = record_kind_prop = SelectProperty("📕유형")
thread_needs_datei_prop = CheckboxFormulaProperty("🛠일정")
stage_is_progress_prop = CheckboxFormulaProperty("🛠진행")
reading_to_main_date_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
reading_to_sch_date_prop = RelationProperty(DatabaseEnum.datei_db.prefix + schedule)
reading_to_start_date_prop = RelationProperty(DatabaseEnum.datei_db.prefix + start)
reading_to_event_prog_prop = RelationProperty(DatabaseEnum.event_db.prefix + progress)
reading_match_date_by_created_time_prop = CheckboxFormulaProperty(
    EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')


def get_earliest_datei(datei_it: Iterable[Page]) -> Page:
    def _get_start_date(datei: Page) -> dt.date | None:
        assert datei.parent == DatabaseEnum.datei_db.entity
        return datei.properties[datei_date_prop].start

    return min([datei for datei in datei_it if _get_start_date(datei)], key=_get_start_date)


def get_earliest_weeki(weeki_it: Iterable[Page]) -> Page:
    def _get_start_date(weeki: Page) -> dt.date | None:
        assert weeki.parent == DatabaseEnum.weeki_db.entity
        return weeki.properties[weeki_date_range_prop].start

    return min([weeki for weeki in weeki_it if _get_start_date(weeki)], key=_get_start_date)

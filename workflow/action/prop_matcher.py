from __future__ import annotations

import datetime as dt
import re
from abc import ABCMeta
from typing import Iterable, Optional, Any

from loguru import logger

from notion_df.core.request import Paginator
from notion_df.entity import Page, Database
from notion_df.object.filter import created_time_filter
from notion_df.object.rich_text import TextSpan, RichText
from notion_df.property import RelationProperty, TitleProperty, PageProperties, DateFormulaPropertyKey, \
    DateProperty, CheckboxFormulaProperty, RichTextProperty, SelectProperty, RelationPagePropertyValue
from notion_df.util.misc import repr_object
from workflow.block_enum import DatabaseEnum
from workflow.core.action import IterableAction
from workflow.emoji_code import EmojiCode

korean_weekday = '월화수목금토일'
record_datetime_auto_key = DateFormulaPropertyKey(EmojiCode.TIMER + '일시')
date_to_week_prop = RelationProperty(DatabaseEnum.week_db.prefix_title)
date_manual_value_prop = DateProperty(EmojiCode.CALENDAR + '날짜')
time_manual_value_prop = RichTextProperty(EmojiCode.CALENDAR + '시간')
date_range_manual_value_prop = DateProperty(EmojiCode.BIG_CALENDAR + '날짜 범위')
event_to_date_prop = RelationProperty(DatabaseEnum.date_db.prefix_title)
event_to_topic_prop = RelationProperty(DatabaseEnum.topic_db.prefix_title)
event_to_issue_prop = RelationProperty(DatabaseEnum.issue_db.prefix_title)
event_to_reading_prop = RelationProperty(DatabaseEnum.reading_db.prefix_title)
"""💛읽기"""
event_to_reading_prog_prop = RelationProperty(DatabaseEnum.reading_db.prefix + '진도')
"""💛진도"""
topic_base_type_prop = SelectProperty("📕유형")
topic_base_type_progress = "🌳진행"
reading_to_main_date_prop = RelationProperty(DatabaseEnum.date_db.prefix_title)
reading_to_start_date_prop = RelationProperty(DatabaseEnum.date_db.prefix + '시작')
reading_to_event_prop = RelationProperty(DatabaseEnum.event_db.prefix_title)
reading_match_date_by_created_time_prop = CheckboxFormulaProperty(EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')


# TODO
#  - 읽기 - 📕유형 <- 꼭지> 추가 (스펙 논의 필요)
#  - 일간/주간 1년 앞서 자동생성

class MatchActionBase:
    def __init__(self):
        self.date_namespace = DateIndex()
        self.week_namespace = WeekIndex()


class MatchAction(IterableAction, metaclass=ABCMeta):
    def __init__(self, base: MatchActionBase):
        self.base = base
        self.date_namespace = base.date_namespace
        self.week_namespace = base.week_namespace
        

class MatchEventProgressForward(MatchAction):
    event_db = DatabaseEnum.event_db.entity

    def __init__(self, base: MatchActionBase):
        super().__init__(base)

    def query_all(self) -> Iterable[Page]:
        return self.event_db.query(filter=(event_to_reading_prop.filter.is_not_empty()
                                           & event_to_reading_prog_prop.filter.is_empty()))

    def _filter(self, event: Page) -> bool:
        return event.data.parent == self.event_db and not event.data.properties[event_to_reading_prog_prop]

    def process_page(self, event: Page) -> Any:
        # TODO: more edge case handling
        if not (len(reading_list := event.data.properties[event_to_reading_prop]) == 1
                and not event.data.properties[event_to_issue_prop]
                and not event.data.properties[event_to_topic_prop]):
            logger.info(f'{event} -> :Skipped')
            return
        reading = reading_list[0]
        event.update(properties=PageProperties({
            event_to_reading_prog_prop: event_to_reading_prog_prop.page_value([reading])
        }))


class MatchEventProgressBackward(MatchAction):
    event_db = DatabaseEnum.event_db.entity

    def __init__(self, base: MatchActionBase):
        super().__init__(base)

    def query_all(self) -> Iterable[Page]:
        return self.event_db.query(filter=(event_to_reading_prop.filter.is_not_empty()
                                           & event_to_reading_prog_prop.filter.is_empty()))

    def _filter(self, event: Page) -> bool:
        return event.data.parent == self.event_db

    def process_page(self, event: Page) -> Any:
        event_readings = event.data.properties[event_to_reading_prop]
        event_readings_new = event_readings + event.data.properties[event_to_reading_prog_prop]
        if event_readings == event_readings_new:
            logger.info(f'{event} -> :Skipped')
            return
        event.update(PageProperties({
            event_to_reading_prop: event_readings_new
        }))


class MatchDateByCreatedTime(MatchAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum, record_to_date: str, *,
                 read_title: bool = False, write_title: bool = False):
        super().__init__(base)
        self.record_db = record.entity
        self.record_to_date = RelationProperty(f'{DatabaseEnum.date_db.prefix}{record_to_date}')
        self.read_title = read_title
        self.write_title = write_title

    def query_all(self) -> Paginator[Page]:
        return self.record_db.query(self.record_to_date.filter.is_empty())

    def _filter(self, record: Page) -> bool:
        return record.data.parent == self.record_db and not record.data.properties[self.record_to_date]

    def process_page(self, record: Page) -> None:
        record_created_date = get_record_created_date(record)
        if self.read_title:
            date = self.date_namespace.by_record_title(record.data.properties.title.plain_text)
            if date is not None:
                # final check if the property value is filled in the meantime
                if record.retrieve().data.properties[self.record_to_date]:
                    logger.info(f'{record} -> :Skipped')
                    return
                record.update(PageProperties({
                    self.record_to_date: self.record_to_date.page_value([date]),
                }))
                logger.info(f'{record} -> {date}')
                return

        date = self.date_namespace.by_date_value(record_created_date)
        properties: PageProperties[RelationPagePropertyValue | RichText] = PageProperties({
            self.record_to_date: self.record_to_date.page_value([date]),
        })
        if self.write_title:
            title = self.date_namespace.format_record_title(record.data.properties.title.plain_text, date)
            properties[record.data.properties.title_prop] = RichText.from_plain_text(title)

        # final check if the property value is filled in the meantime
        if record.retrieve().data.properties[self.record_to_date]:
            logger.info(f'{record} -> :Skipped')
            return
        record.update(properties)
        logger.info(f'{record} -> {date}')
        return


class MatchTimeManualValue(MatchAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum, record_to_date: str):
        super().__init__(base)
        self.record_db = Database(record.id)
        self.record_to_date = RelationProperty(DatabaseEnum.date_db.prefix + record_to_date)

    def query_all(self) -> Iterable[Page]:
        # since the benefits are concentrated on near present days,
        # we could easily limit query_all() with today without lamentations
        return self.record_db.query(time_manual_value_prop.filter.is_empty()
                                    & created_time_filter.equals(dt.date.today()))

    def _filter(self, record: Page) -> bool:
        if not (record.data.parent == self.record_db and not record.data.properties[time_manual_value_prop]):
            return False
        try:
            record_date = record.data.properties[self.record_to_date][0]
        except IndexError:
            return True
        record_date_value = record_date.data.properties[date_manual_value_prop].start
        return record.data.created_time.date() == record_date_value

    def process_page(self, record: Page) -> None:
        def _process_page() -> Optional[str]:
            time_manual_value = record.data.created_time.strftime('%H:%M')
            if record.retrieve().data.properties[time_manual_value_prop]:
                return
            record.update(PageProperties({
                time_manual_value_prop: time_manual_value_prop.page_value([TextSpan(time_manual_value)])}))
            return time_manual_value

        _date = _process_page()
        logger.info(f'{record} -> {_date if _date else ":Skipped"}')


class MatchReadingsStartDate(MatchAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.reading_db = DatabaseEnum.reading_db.entity
        self.event_db = DatabaseEnum.event_db.entity

    def query_all(self) -> Paginator[Page]:
        return self.reading_db.query(
            reading_to_start_date_prop.filter.is_empty() & (
                    reading_to_event_prop.filter.is_not_empty()
                    | reading_to_main_date_prop.filter.is_not_empty()
                    | reading_match_date_by_created_time_prop.filter.is_not_empty()
            )
        )

    def _filter(self, page: Page) -> bool:
        return (page.data.parent == self.reading_db and not page.data.properties[reading_to_start_date_prop]
                and (page.data.properties[reading_to_event_prop]
                     or page.data.properties[reading_match_date_by_created_time_prop]))

    def process_page(self, reading: Page):
        def find_date():
            def get_reading_event_dates() -> Iterable[Page]:
                reading_events = reading.data.properties[reading_to_event_prop]
                # TODO: RollupPagePropertyValue 구현 후 이곳을 간소화
                for event in reading_events:
                    if not (date_list := event.get_data().properties[event_to_date_prop]):
                        continue
                    date = date_list[0]
                    if date.get_data().properties[date_manual_value_prop] is None:
                        continue
                    yield date

            if reading_event_and_main_dates := {*get_reading_event_dates(),
                                                *reading.data.properties[reading_to_main_date_prop]}:
                return get_earliest_date(reading_event_and_main_dates)
            if reading.data.properties[reading_match_date_by_created_time_prop]:
                reading_created_date = get_record_created_date(reading)
                return self.date_namespace.by_date_value(reading_created_date)

        def _process_page() -> Optional[Page]:
            date = find_date()
            if not date:
                return
            # final check if the property value is filled in the meantime
            if reading.retrieve().data.properties[reading_to_start_date_prop]:
                return
            reading.update(PageProperties({reading_to_start_date_prop: reading_to_start_date_prop.page_value([date])}))
            return date

        _date = _process_page()
        logger.info(f'{reading} -> {_date if _date else ": Skipped"}')


class MatchWeekByRefDate(MatchAction):
    def __init__(self, base: MatchActionBase, record_db_enum: DatabaseEnum,
                 record_to_week: str, record_to_date: str):
        super().__init__(base)
        self.record_db = record_db_enum.entity
        self.record_db_title = self.record_db.data.title = record_db_enum.title
        self.record_to_week = RelationProperty(f'{DatabaseEnum.week_db.prefix}{record_to_week}')
        self.record_to_date = RelationProperty(f'{DatabaseEnum.date_db.prefix}{record_to_date}')

    def __repr__(self):
        return repr_object(self,
                           record_db_title=self.record_db_title,
                           record_to_week=self.record_to_week,
                           record_to_date=self.record_to_date)

    def query_all(self) -> Paginator[Page]:
        return self.record_db.query(
            self.record_to_week.filter.is_empty() & self.record_to_date.filter.is_not_empty())

    def _filter(self, page: Page) -> bool:
        return page.data.parent == self.record_db and page.data.properties[self.record_to_date]

    def process_page(self, record: Page) -> None:
        def _process_page():
            new_record_weeks = self.record_to_week.page_value()
            for record_date in record.data.properties[self.record_to_date]:
                if not record_date.data:
                    record_date.retrieve()
                new_record_weeks.append(record_date.data.properties[date_to_week_prop][0])

            # final check if the property value is filled or changed in the meantime
            prev_record_weeks = record.data.properties[self.record_to_week]
            if set(prev_record_weeks) == set(new_record_weeks):
                return

            curr_record_weeks = record.retrieve().data.properties[self.record_to_week]
            if ((set(prev_record_weeks) != set(curr_record_weeks))
                    or (set(curr_record_weeks) == set(new_record_weeks))):
                return
            record.update(PageProperties({self.record_to_week: new_record_weeks}))
            return new_record_weeks

        _weeks = _process_page()
        logger.info(f'{record} -> {list(_weeks) if _weeks else ": Skipped"}')


class MatchWeekByDateValue(MatchAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.date_db = DatabaseEnum.date_db.entity

    def __repr__(self):
        return repr_object(self)

    def query_all(self) -> Paginator[Page]:
        return self.date_db.query(date_to_week_prop.filter.is_empty())

    def _filter(self, page: Page) -> bool:
        return page.data.parent == self.date_db and not page.data.properties[date_to_week_prop]

    def process_page(self, date: Page):
        date_value = date.data.properties[date_manual_value_prop]
        if not date_value:
            logger.info(f'{date} -> Skipped')
            return
        week = self.week_namespace.get_by_date_value(date_value.start)
        if date.retrieve().data.properties[date_to_week_prop]:
            return
        date.update(PageProperties({date_to_week_prop: date_to_week_prop.page_value([week])}))
        logger.info(f'{date} -> {week}')


class DeprMatchTopic(MatchAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum, ref: DatabaseEnum,
                 record_to_ref_prop_name: str, record_to_topic_prop_name: str, ref_to_topic_prop_name: str):
        super().__init__(base)
        self.record_db = record.entity
        self.ref_db = ref.entity
        self.record_to_ref_prop = RelationProperty(record_to_ref_prop_name)
        self.record_to_topic_prop = RelationProperty(record_to_topic_prop_name)
        self.ref_to_topic_prop = RelationProperty(ref_to_topic_prop_name)

    def query_all(self) -> Iterable[Page]:
        return self.record_db.query(self.record_to_ref_prop.filter.is_not_empty())

    def _filter(self, record: Page) -> bool:
        return bool(record.data.parent == self.record_db and record.data.properties[self.record_to_ref_prop])

    def process_page(self, record: Page) -> None:
        # rewrite so that it utilizes the RelationPagePropertyValue's feature 
        #  (rather than based on builtin list and set)
        curr_topic_list: list[Page] = list(record.data.properties[self.record_to_topic_prop])
        new_topic_set: set[Page] = set(curr_topic_list)
        for ref in record.data.properties[self.record_to_ref_prop]:
            ref_topic_set = {topic for topic in ref.get_data().properties[self.ref_to_topic_prop]
                             if topic.get_data().properties[topic_base_type_prop] == topic_base_type_progress}
            if set(curr_topic_list) & ref_topic_set:
                continue
            new_topic_set.update(ref_topic_set)
        if not new_topic_set - set(curr_topic_list):
            return
        curr_topic_list = list(record.retrieve().data.properties[self.record_to_topic_prop])
        new_topic = curr_topic_list + list(new_topic_set)
        record.update(PageProperties({
            self.record_to_topic_prop: self.record_to_topic_prop.page_value(new_topic)}))


# TODO: rename DatabaseNamespace
class DatabaseIndex(metaclass=ABCMeta):
    def __init__(self, database: DatabaseEnum, title_prop: str):
        self.database = database.entity
        self.title_prop = TitleProperty(title_prop)
        self.pages_by_title_plain_text: dict[str, Page] = {}

    def by_title(self, title_plain_text: str) -> Page:
        if not (page := self.pages_by_title_plain_text.get(title_plain_text)):
            date_list = self.database.query(self.title_prop.filter.equals(title_plain_text))
            if date_list:
                page = date_list[0]
            else:
                page = self.database.create_child_page(PageProperties({
                    self.title_prop: self.title_prop.page_value.from_plain_text(title_plain_text)
                }))
            self.pages_by_title_plain_text[page.data.properties.title.plain_text] = page
        return page


# TODO: rename DateINamespace
class DateIndex(DatabaseIndex):
    def __init__(self):
        super().__init__(DatabaseEnum.date_db, EmojiCode.GREEN_BOOK + '제목')

    def by_date_value(self, date_value: dt.date) -> Page:
        day_name = korean_weekday[date_value.weekday()] + '요일'
        title_plain_text = f'{date_value.strftime("%y%m%d")} {day_name}'
        return self.by_title(title_plain_text)

    def by_record_title(self, title_plain_text: str) -> Optional[Page]:
        date_value = self._get_record_date_value(title_plain_text)
        if date_value is None:
            return
        return self.by_date_value(date_value)

    @classmethod
    def format_record_title(cls, title_plain_text: str, date: Page) -> Optional[str]:
        if cls._get_record_date_value(title_plain_text):
            return None
        date_value = date.data.properties[date_manual_value_prop].start
        return f'{date_value.strftime("%y%m%d")}| {title_plain_text}'

    @classmethod
    def _get_record_date_value(cls, title_plain_text: str) -> Optional[dt.date]:
        pattern = r'^(\d{2})(\d{2})(\d{2}).*'
        match = re.match(pattern, title_plain_text)

        if not match:
            return None
        year, month, day = match.groups()
        if year > 90:  # TODO
            return None
        try:
            return dt.date(2000 + year, month, day)
        except ValueError:
            # In case the date is not valid (like '000229' for non-leap year)
            return None


class WeekIndex(DatabaseIndex):
    def __init__(self):
        super().__init__(DatabaseEnum.week_db, EmojiCode.GREEN_BOOK + '제목')

    def get_by_date_value(self, date_value: dt.date) -> Page:
        title_plain_text = self.first_day_of_week(date_value).strftime("%y/%U")
        return self.by_title(title_plain_text)

    @classmethod
    def first_day_of_week(cls, date_value: dt.date) -> dt.date:
        # returns the first day (sunday) of the week.
        weekday = (date_value.weekday() + 1) % 7
        return date_value + dt.timedelta(days=-weekday)

    @classmethod
    def last_day_of_week(cls, date_value: dt.date) -> dt.date:
        return cls.first_day_of_week(date_value) + dt.timedelta(days=6)


def get_record_created_date(record: Page) -> dt.date:
    # TODO: '📆일시' parsing 지원
    return (record.get_data().created_time + dt.timedelta(hours=-5)).date()


def get_earliest_date(dates: Iterable[Page]) -> Page:
    """only works for children of `DatabaseEnum.date_db` or `week_db`"""

    def _get_start_date(date: Page) -> dt.date:
        parent_db = DatabaseEnum.from_entity(date.get_data().parent)
        if parent_db == DatabaseEnum.date_db:
            prop = date_manual_value_prop
        elif parent_db == DatabaseEnum.week_db:
            prop = date_range_manual_value_prop
        else:
            raise ValueError(date)
        return date.get_data().properties[prop].start

    return min(dates, key=_get_start_date)

from __future__ import annotations

import datetime as dt
from abc import ABCMeta
from typing import Optional, cast
from uuid import UUID

from notion_df.entity import Namespace, Page
from notion_df.property import RelationProperty, TitleProperty, PageProperties, DateFormulaPropertyKey, \
    DateProperty, CheckboxFormulaProperty
from notion_df.util.misc import get_url
from workflow.constant.block_enum import DatabaseEnum
from workflow.constant.emoji_code import EmojiCode
from workflow.util.action import Action

korean_weekday = '월화수목금토일'
record_datetime_auto = DateFormulaPropertyKey(EmojiCode.TIMER + '일시')
date_to_week = RelationProperty(DatabaseEnum.weeks.prefix_title)
date_manual_value = DateProperty(EmojiCode.CALENDAR + '날짜')
event_to_date = RelationProperty(DatabaseEnum.dates.prefix_title)
reading_to_date = RelationProperty(DatabaseEnum.dates.prefix + '시작')
reading_to_event = RelationProperty(DatabaseEnum.events.prefix_title)
reading_match_date_by_created_time = CheckboxFormulaProperty(EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')


def get_record_created_date(record: Page) -> dt.date:
    # TODO: '📆일시' parsing 지원
    return (record.created_time + dt.timedelta(hours=-5)).date()


class MatcherWorkspace:
    def __init__(self, namespace: Namespace):
        self.namespace = namespace
        self.date_namespace = DateIndex(namespace)
        self.week_namespace = WeekIndex(namespace)


class MatchAction(Action, metaclass=ABCMeta):
    def __init__(self, workspace: MatcherWorkspace):
        self.workspace = workspace
        self.namespace = workspace.namespace
        self.date_namespace = workspace.date_namespace
        self.week_namespace = workspace.week_namespace


class MatchDateByCreatedTime(MatchAction):
    def __init__(self, workspace: MatcherWorkspace, records: DatabaseEnum, record_to_date: str):
        super().__init__(workspace)
        self.records = self.namespace.database(records.id)
        self.record_to_date = RelationProperty(f'{DatabaseEnum.dates.prefix}{record_to_date}')

    def execute(self):
        record_list = self.records.query(self.record_to_date.filter.is_empty())
        for record in record_list:
            date = self.process_page(record)
            print(f'"{record.properties.title.plain_text} ({record.url})"'
                  + (f'-> "{date.properties.title.plain_text}"' if date else ': Skipped'))

    def process_page(self, record: Page) -> Optional[Page]:
        record_created_date = get_record_created_date(record)
        date = self.date_namespace.get_by_date_value(record_created_date)

        # final check if the property value is filled in the meantime
        # TODO: add the logic that 'if user edited the page recently(<30s), do not edit'
        #  - need to support user endpoint (we need to retrieve user from PartialUser.id)
        if record.retrieve().properties[self.record_to_date]:
            return
        record.update(PageProperties({self.record_to_date: self.record_to_date.page_value([date.id])}))
        return date


class MatchReadingsStartDate(MatchAction):
    def __init__(self, workspace: MatcherWorkspace):
        super().__init__(workspace)
        self.readings = self.namespace.database(DatabaseEnum.readings.id)
        self.events = self.namespace.database(DatabaseEnum.events.id)

    def execute(self):
        event_list = self.readings.query(
            reading_to_date.filter.is_empty() & (
                    reading_to_event.filter.is_not_empty()
                    | reading_match_date_by_created_time.filter.is_not_empty()
            )
        )
        for event in event_list:
            date = self.process_page(event)
            print(f'"{event.properties.title.plain_text} ({event.url})"'
                  + (f'-> "{date.properties.title.plain_text}"' if date else ': Skipped'))

    def process_page(self, reading: Page) -> Optional[Page]:
        reading_event_ids = reading.properties[reading_to_event]
        dates = []
        # TODO: RollupPagePropertyValue 구현 후 이곳을 간소화
        for event_id in reading_event_ids:
            event = self.namespace.page(event_id)
            if not event.timestamp:
                event.retrieve()
            event_date_ids = event.properties[event_to_date]
            if not event_date_ids:
                continue
            date = self.namespace.page(event_date_ids[0])
            if not date.timestamp:
                date.retrieve()
            if date.properties[date_manual_value] is None:
                continue
            dates.append(date)
        if dates:
            # noinspection PyShadowingNames
            date = min(dates, key=lambda date: cast(Page, date).properties[date_manual_value].start)
        elif not reading.properties[reading_match_date_by_created_time]:
            return
        else:
            reading_created_date = get_record_created_date(reading)
            date = self.date_namespace.get_by_date_value(reading_created_date)
        # final check if the property value is filled in the meantime
        if reading.retrieve().properties[reading_to_date]:
            return
        reading.update(PageProperties({reading_to_date: reading_to_date.page_value([date.id])}))


class MatchWeekByDate(MatchAction):
    def __init__(self, workspace: MatcherWorkspace, records: DatabaseEnum,
                 record_to_week: str, record_to_date: str):
        super().__init__(workspace)
        self.records = self.namespace.database(records.id)
        self.record_to_week = RelationProperty(f'{DatabaseEnum.weeks.prefix}{record_to_week}')
        self.record_to_date = RelationProperty(f'{DatabaseEnum.dates.prefix}{record_to_date}')

    def execute(self):
        record_list = self.records.query(
            self.record_to_week.filter.is_empty() & self.record_to_date.filter.is_not_empty())
        for record in record_list:
            week_id = self.process_page(record)
            print(f'"{record.properties.title.plain_text} ({record.url})"'
                  + (f'-> "{get_url(week_id, "dyhn")}"' if week_id else ': Skipped'))

    def process_page(self, event: Page) -> Optional[UUID]:
        event_date_id = event.properties[self.record_to_date][0]
        event_date = self.namespace.page(event_date_id)
        if not event_date.timestamp:
            event_date.retrieve()
        event_week_id = event_date.properties[date_to_week][0]

        # final check if the property value is filled in the meantime
        if event.retrieve().properties[self.record_to_week]:
            return
        event.update(PageProperties({self.record_to_week: self.record_to_week.page_value([event_week_id])}))
        return event_week_id


class MatchWeekByDateValue(MatchAction):
    def __init__(self, workspace: MatcherWorkspace):
        super().__init__(workspace)
        self.dates = self.namespace.database(DatabaseEnum.dates.id)

    def execute(self):
        date_list = self.dates.query(date_to_week.filter.is_empty())
        for date in date_list:
            date_value = date.properties[date_manual_value]
            week = self.week_namespace.get_by_date_value(date_value.start)
            if date.retrieve().properties[date_to_week]:
                continue
            date.update(PageProperties({date_to_week: date_to_week.page_value([week.id])}))
            print(f'"{date.properties.title.plain_text} ({date.url})" -> '
                  f'"{week.properties.title.plain_text} ({week.url})"')


class DatabaseIndex(metaclass=ABCMeta):
    def __init__(self, namespace: Namespace, database: DatabaseEnum, title: str):
        self.namespace = namespace
        self.database = namespace.database(database.id)
        self.title = TitleProperty(title)
        self.pages_by_title_plain_text: dict[str, Page] = {}

    def get_by_title_plain_text(self, title_plain_text: str) -> Page:
        if not (page := self.pages_by_title_plain_text.get(title_plain_text)):
            date_list = self.database.query(self.title.filter.equals(title_plain_text))
            if date_list:
                page = date_list[0]
            else:
                page = self.database.create_child_page(PageProperties({
                    self.title: self.title.page_value.from_plain_text(title_plain_text)
                }))
            self.pages_by_title_plain_text[page.properties.title.plain_text] = page
        return page


class DateIndex(DatabaseIndex):
    def __init__(self, namespace: Namespace):
        super().__init__(namespace, DatabaseEnum.dates, f'{EmojiCode.GREEN_BOOK}제목')

    def get_by_date_value(self, date_value: dt.date) -> Page:
        day_name = korean_weekday[date_value.weekday()] + '요일'
        title_plain_text = f'{date_value.strftime("%y%m%d")} {day_name}'
        return self.get_by_title_plain_text(title_plain_text)


class WeekIndex(DatabaseIndex):
    def __init__(self, namespace: Namespace):
        super().__init__(namespace, DatabaseEnum.weeks, EmojiCode.GREEN_BOOK + '제목')

    def get_by_date_value(self, date_value: dt.date) -> Page:
        title_plain_text = self.first_day_of_week(date_value).strftime("%y/%U")
        return self.get_by_title_plain_text(title_plain_text)

    @classmethod
    def first_day_of_week(cls, date_value: dt.date) -> dt.date:
        # returns the first day (sunday) of the week.
        weekday = (date_value.weekday() + 1) % 7
        return date_value + dt.timedelta(days=-weekday)

    @classmethod
    def last_day_of_week(cls, date_value: dt.date) -> dt.date:
        return cls.first_day_of_week(date_value) + dt.timedelta(days=6)

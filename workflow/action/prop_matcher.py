from __future__ import annotations

import datetime as dt
from abc import ABCMeta
from typing import cast

from notion_df.entity import Page, Database
from notion_df.object.property import RelationProperty, TitleProperty, PageProperties, DateFormulaPropertyKey, \
    DateProperty, CheckboxFormulaProperty
from notion_df.util.collection import Paginator
from notion_df.util.misc import repr_object
from notion_df.variable import my_tz, Settings
from workflow.action.action_core import Action, IterableAction
from workflow.constant.block_enum import DatabaseEnum
from workflow.constant.emoji_code import EmojiCode

korean_weekday = '월화수목금토일'
record_datetime_auto = DateFormulaPropertyKey(EmojiCode.TIMER + '일시')
date_to_week = RelationProperty(DatabaseEnum.week_db.prefix_title)
date_manual_value = DateProperty(EmojiCode.CALENDAR + '날짜')
event_to_date = RelationProperty(DatabaseEnum.date_db.prefix_title)
reading_to_date = RelationProperty(DatabaseEnum.date_db.prefix + '시작')
reading_to_event = RelationProperty(DatabaseEnum.event_db.prefix_title)
reading_match_date_by_created_time = CheckboxFormulaProperty(EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')


def get_record_created_date(record: Page) -> dt.date:
    # TODO: '📆일시' parsing 지원
    return (record.created_time + dt.timedelta(hours=-5)).date()


class MatchActionBase:
    def __init__(self):
        self.date_namespace = DateIndex()
        self.week_namespace = WeekIndex()


class MatchAction(Action, metaclass=ABCMeta):
    def __init__(self, base: MatchActionBase):
        self.base = base
        self.date_namespace = base.date_namespace
        self.week_namespace = base.week_namespace


class MatchDateByCreatedTime(MatchAction, IterableAction):
    def __init__(self, base: MatchActionBase, records: DatabaseEnum, record_to_date: str):
        super().__init__(base)
        self.record_db = Database(records.id)
        self.record_to_date = RelationProperty(f'{DatabaseEnum.date_db.prefix}{record_to_date}')

    def query_all(self) -> Paginator[Page]:
        return self.record_db.query(self.record_to_date.filter.is_empty())

    def filter(self, page: Page) -> bool:
        return page.parent == self.record_db and not page.properties[self.record_to_date]

    def process_page(self, record: Page):
        def wrapper():
            record_created_date = get_record_created_date(record)
            date = self.date_namespace.get_by_date_value(record_created_date)

            # final check if the property value is filled in the meantime
            if record.retrieve().properties[self.record_to_date]:
                return
            record.update(PageProperties({self.record_to_date: self.record_to_date.page_value([date])}))
            return date

        _date = wrapper()
        print(f'\t{record}\n\t\t-> {_date if _date else ":Skipped"}')


class MatchReadingsStartDate(MatchAction, IterableAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.reading_db = Database(DatabaseEnum.reading_db.id)
        self.event_db = Database(DatabaseEnum.event_db.id)

    def query_all(self) -> Paginator[Page]:
        return self.reading_db.query(
            reading_to_date.filter.is_empty() & (
                    reading_to_event.filter.is_not_empty()
                    | reading_match_date_by_created_time.filter.is_not_empty()
            )
        )

    def filter(self, page: Page) -> bool:
        return (page.parent == self.reading_db and not page.properties[reading_to_date]
                and (page.properties[reading_to_event]
                     or page.properties[reading_match_date_by_created_time]))

    def process_page(self, reading: Page):
        def find_date():
            reading_events = reading.properties[reading_to_event]
            dates = []
            # TODO: RollupPagePropertyValue 구현 후 이곳을 간소화
            for event in reading_events:
                if not event.last_timestamp:
                    event.retrieve()
                if not (date_list := event.properties[event_to_date]):
                    continue
                date = date_list[0]
                if not date.last_timestamp:
                    date.retrieve()
                if date.properties[date_manual_value] is None:
                    continue
                dates.append(date)
            if dates:
                # noinspection PyShadowingNames
                return min(dates, key=lambda date: cast(Page, date).properties[date_manual_value].start)
            if reading.properties[reading_match_date_by_created_time]:
                reading_created_date = get_record_created_date(reading)
                return self.date_namespace.get_by_date_value(reading_created_date)

        def wrapper():
            date = find_date()
            if not date:
                return
            # final check if the property value is filled in the meantime
            if reading.retrieve().properties[reading_to_date]:
                return
            reading.update(PageProperties({reading_to_date: reading_to_date.page_value([date])}))
            return date

        _date = wrapper()
        print(f'\t{reading}\n\t\t-> {_date if _date else ": Skipped"}')


class MatchWeekByRefDate(MatchAction, IterableAction):
    def __init__(self, base: MatchActionBase, record_db_enum: DatabaseEnum,
                 record_to_week: str, record_to_date: str):
        super().__init__(base)
        self.record_db = Database(record_db_enum.id)
        self.record_db_title = self.record_db.title = record_db_enum.title
        self.record_to_week = RelationProperty(f'{DatabaseEnum.week_db.prefix}{record_to_week}')
        self.record_to_date = RelationProperty(f'{DatabaseEnum.date_db.prefix}{record_to_date}')

    def __repr__(self):
        return repr_object(self, ['record_db_title', 'record_to_week', 'record_to_date'])

    def query_all(self) -> Paginator[Page]:
        return self.record_db.query(
            self.record_to_week.filter.is_empty() & self.record_to_date.filter.is_not_empty())

    def filter(self, page: Page) -> bool:
        return (page.parent == self.record_db and not page.properties[self.record_to_week]
                and page.properties[self.record_to_date])

    def process_page(self, record: Page):
        def wrapper():
            record_date = record.properties[self.record_to_date][0]
            if not record_date.last_timestamp:
                record_date.retrieve()
            record_week = record_date.properties[date_to_week][0]

            # final check if the property value is filled in the meantime
            if record.retrieve().properties[self.record_to_week]:
                return
            record.update(PageProperties({self.record_to_week: self.record_to_week.page_value([record_week])}))
            return record_week

        _week = wrapper()
        print(f'\t{record}\n\t\t-> {_week if _week else ": Skipped"}')


class MatchWeekByDateValue(MatchAction, IterableAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.date_db = Database(DatabaseEnum.date_db.id)

    def __repr__(self):
        return repr_object(self, [])

    def query_all(self) -> Paginator[Page]:
        return self.date_db.query(date_to_week.filter.is_empty())

    def filter(self, page: Page) -> bool:
        return page.parent == self.date_db and not page.properties[date_to_week]

    def process_page(self, date: Page):
        date_value = date.properties[date_manual_value]
        if not date_value:
            print(f'\t{date} -> Skipped')
        week = self.week_namespace.get_by_date_value(date_value.start)
        if date.retrieve().properties[date_to_week]:
            return
        date.update(PageProperties({date_to_week: date_to_week.page_value([week])}))
        print(f'\t{date}\n\t\t-> {week}')


class DatabaseIndex(metaclass=ABCMeta):
    def __init__(self, database: DatabaseEnum, title: str):
        self.database = Database(database.id)
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
    def __init__(self):
        super().__init__(DatabaseEnum.date_db, f'{EmojiCode.GREEN_BOOK}제목')

    def get_by_date_value(self, date_value: dt.date) -> Page:
        day_name = korean_weekday[date_value.weekday()] + '요일'
        title_plain_text = f'{date_value.strftime("%y%m%d")} {day_name}'
        return self.get_by_title_plain_text(title_plain_text)


class WeekIndex(DatabaseIndex):
    def __init__(self):
        super().__init__(DatabaseEnum.week_db, EmojiCode.GREEN_BOOK + '제목')

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


if __name__ == '__main__':
    _base = MatchActionBase()
    now = dt.datetime.now().astimezone(my_tz)
    with Settings.print:
        _action = MatchReadingsStartDate(_base)
        Action.execute_by_last_edited_time([_action], now - dt.timedelta(hours=1))
    # Action.execute_by_last_edited_time([MatchDateByCreatedTime(_base, DatabaseEnum.event_db, '일간')],
    #                                    now - dt.timedelta(hours=2), now)

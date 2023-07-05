from __future__ import annotations

import datetime as dt
from abc import ABCMeta
from typing import cast, Iterable, Optional

from notion_df.core.request import Paginator
from notion_df.entity import Page, Database
from notion_df.object.filter import created_time_filter
from notion_df.object.rich_text import TextSpan
from notion_df.property import RelationProperty, TitleProperty, PageProperties, DateFormulaPropertyKey, \
    DateProperty, CheckboxFormulaProperty, RichTextProperty
from notion_df.util.misc import repr_object
from workflow.action.action_core import IterableAction
from workflow.constant.block_enum import DatabaseEnum
from workflow.constant.emoji_code import EmojiCode

korean_weekday = '월화수목금토일'
record_datetime_auto_key = DateFormulaPropertyKey(EmojiCode.TIMER + '일시')
date_to_week_prop = RelationProperty(DatabaseEnum.week_db.prefix_title)
date_manual_value_prop = DateProperty(EmojiCode.CALENDAR + '날짜')
time_manual_value_prop = RichTextProperty(EmojiCode.CALENDAR + '시간')
event_to_date_prop = RelationProperty(DatabaseEnum.date_db.prefix_title)
event_to_stream_prop = RelationProperty(DatabaseEnum.topic_db.prefix_title)
event_to_issue_prop = RelationProperty(DatabaseEnum.issue_db.prefix_title)
reading_to_main_date_prop = RelationProperty(DatabaseEnum.date_db.prefix_title)
reading_to_start_date_prop = RelationProperty(DatabaseEnum.date_db.prefix + '시작')
reading_to_event_prop = RelationProperty(DatabaseEnum.event_db.prefix_title)
reading_match_date_by_created_time_prop = CheckboxFormulaProperty(EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')


def get_record_created_date(record: Page) -> dt.date:
    # TODO: '📆일시' parsing 지원
    return (record.created_time + dt.timedelta(hours=-5)).date()


class MatchActionBase:
    def __init__(self):
        self.date_namespace = DateIndex()
        self.week_namespace = WeekIndex()


class MatchAction(IterableAction, metaclass=ABCMeta):
    def __init__(self, base: MatchActionBase):
        self.base = base
        self.date_namespace = base.date_namespace
        self.week_namespace = base.week_namespace


class MatchDateByCreatedTime(MatchAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum, record_to_date: str):
        super().__init__(base)
        self.record_db = Database(record.id)
        self.record_to_date = RelationProperty(f'{DatabaseEnum.date_db.prefix}{record_to_date}')

    def query_all(self) -> Paginator[Page]:
        return self.record_db.query(self.record_to_date.filter.is_empty())

    def filter(self, record: Page) -> bool:
        return record.parent == self.record_db and not record.properties[self.record_to_date]

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


class MatchReadingsStartDate(MatchAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.reading_db = Database(DatabaseEnum.reading_db.id)
        self.event_db = Database(DatabaseEnum.event_db.id)

    def query_all(self) -> Paginator[Page]:
        return self.reading_db.query(
            reading_to_start_date_prop.filter.is_empty() & (
                    reading_to_event_prop.filter.is_not_empty()
                    | reading_to_main_date_prop.filter.is_not_empty()
                    | reading_match_date_by_created_time_prop.filter.is_not_empty()
            )
        )

    def filter(self, page: Page) -> bool:
        return (page.parent == self.reading_db and not page.properties[reading_to_start_date_prop]
                and (page.properties[reading_to_event_prop]
                     or page.properties[reading_match_date_by_created_time_prop]))

    def process_page(self, reading: Page):
        def find_date():
            def get_earliest_date(dates: Iterable[Page]) -> Page:
                return min(dates, key=lambda _date: cast(Page, _date).properties[date_manual_value_prop].start)

            def get_reading_event_dates() -> Iterable[Page]:
                reading_events = reading.properties[reading_to_event_prop]
                # TODO: RollupPagePropertyValue 구현 후 이곳을 간소화
                for event in reading_events:
                    if not event.last_timestamp:
                        event.retrieve()
                    if not (date_list := event.properties[event_to_date_prop]):
                        continue
                    date = date_list[0]
                    if not date.last_timestamp:
                        date.retrieve()
                    if date.properties[date_manual_value_prop] is None:
                        continue
                    yield date

            if reading_event_and_main_dates := {*get_reading_event_dates(),
                                                *reading.properties[reading_to_main_date_prop]}:
                return get_earliest_date(reading_event_and_main_dates)
            if reading.properties[reading_match_date_by_created_time_prop]:
                reading_created_date = get_record_created_date(reading)
                return self.date_namespace.get_by_date_value(reading_created_date)

        def _process_page() -> Optional[Page]:
            date = find_date()
            if not date:
                return
            # final check if the property value is filled in the meantime
            if reading.retrieve().properties[reading_to_start_date_prop]:
                return
            reading.update(PageProperties({reading_to_start_date_prop: reading_to_start_date_prop.page_value([date])}))
            return date

        _date = _process_page()
        print(f'\t{reading}\n\t\t-> {_date if _date else ": Skipped"}')


class MatchWeekByRefDate(MatchAction):
    def __init__(self, base: MatchActionBase, record_db_enum: DatabaseEnum,
                 record_to_week: str, record_to_date: str):
        super().__init__(base)
        self.record_db = Database(record_db_enum.id)
        self.record_db_title = self.record_db.title = record_db_enum.title
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

    def filter(self, page: Page) -> bool:
        return page.parent == self.record_db and page.properties[self.record_to_date]

    def process_page(self, record: Page) -> None:
        def _process_page():
            new_record_weeks = self.record_to_week.page_value()
            for record_date in record.properties[self.record_to_date]:
                if not record_date.last_response:
                    record_date.retrieve()
                new_record_weeks.append(record_date.properties[date_to_week_prop][0])

            # final check if the property value is filled in the meantime
            if record.properties[self.record_to_week] != record.retrieve().properties[self.record_to_week]:
                return
            record.update(PageProperties({self.record_to_week: new_record_weeks}))
            return new_record_weeks

        _weeks = _process_page()
        print(f'\t{record}\n\t\t-> {list(_weeks) if _weeks else ": Skipped"}')


class MatchWeekByDateValue(MatchAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.date_db = Database(DatabaseEnum.date_db.id)

    def __repr__(self):
        return repr_object(self)

    def query_all(self) -> Paginator[Page]:
        return self.date_db.query(date_to_week_prop.filter.is_empty())

    def filter(self, page: Page) -> bool:
        return page.parent == self.date_db and not page.properties[date_to_week_prop]

    def process_page(self, date: Page):
        date_value = date.properties[date_manual_value_prop]
        if not date_value:
            print(f'\t{date} -> Skipped')
            return
        week = self.week_namespace.get_by_date_value(date_value.start)
        if date.retrieve().properties[date_to_week_prop]:
            return
        date.update(PageProperties({date_to_week_prop: date_to_week_prop.page_value([week])}))
        print(f'\t{date}\n\t\t-> {week}')


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

    def filter(self, record: Page) -> bool:
        if not (record.parent == self.record_db and not record.properties[time_manual_value_prop]):
            return False
        try:
            record_date = record.properties[self.record_to_date][0]
        except IndexError:
            return True
        record_date_value = record_date.properties[date_manual_value_prop].start
        return record.created_time.date() == record_date_value

    def process_page(self, record: Page) -> None:
        def _process_page() -> Optional[str]:
            time_manual_value = record.created_time.strftime('%H:%M')
            if record.retrieve().properties[time_manual_value_prop]:
                return
            record.update(PageProperties({
                time_manual_value_prop: time_manual_value_prop.page_value([TextSpan(time_manual_value)])}))
            return time_manual_value

        _date = _process_page()
        print(f'\t{record}\n\t\t-> {_date if _date else ":Skipped"}')


class MatchStream(MatchAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum, ref: DatabaseEnum,
                 record_to_ref_prop_name: str, record_to_stream_prop_name: str, ref_to_stream_prop_name: str):
        super().__init__(base)
        self.record_db = record.entity
        self.ref_db = ref.entity
        self.record_to_ref_prop = RelationProperty(record_to_ref_prop_name)
        self.record_to_stream_prop = RelationProperty(record_to_stream_prop_name)
        self.ref_to_stream_prop = RelationProperty(ref_to_stream_prop_name)

    def query_all(self) -> Iterable[Page]:
        return self.record_db.query(self.record_to_ref_prop.filter.is_not_empty())

    def filter(self, record: Page) -> bool:
        return bool(record.parent == self.record_db and record.properties[self.record_to_ref_prop])

    def process_page(self, record: Page) -> None:
        curr_stream_list: list[Page] = record.properties[self.record_to_stream_prop]
        new_stream_set: set[Page] = set(curr_stream_list)
        for ref in record.properties[self.record_to_ref_prop]:
            if not ref.last_response:
                ref.retrieve()
            ref_stream_set = set(ref.properties[self.ref_to_stream_prop])
            for stream in ref_stream_set:
                if not stream.last_response:
                    stream.retrieve()
            ref_stream_set = {stream for stream in ref_stream_set
                              if stream.properties["📕유형"] == "🌳진행"}  # TODO: define property variable
            ref_stream_set.difference_update(curr_stream_list)
            if set(curr_stream_list) & ref_stream_set:
                continue
            new_stream_set.update(ref_stream_set)
        new_stream_set.difference_update(curr_stream_list)
        if not new_stream_set:
            return
        new_stream = curr_stream_list + list(new_stream_set)
        record.update(PageProperties({self.record_to_stream_prop: self.record_to_stream_prop.page_value(new_stream)}))


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
    pass
    # from notion_df.variable import my_tz, Settings
    # _base = MatchActionBase()
    # now = dt.datetime.now().astimezone(my_tz)
    #
    # with Settings.print:
    #     _action = MatchStream.get_actions(_base)[0]
    #     _action.execute_all()
    #
    # with Settings.print:
    #     _action = MatchReadingsStartDate(_base)
    #     Action.execute_by_last_edited_time([_action], now - dt.timedelta(hours=1))
    # Action.execute_by_last_edited_time([MatchDateByCreatedTime(_base, DatabaseEnum.event_db, '일간')],
    #                                    now - dt.timedelta(hours=2), now)

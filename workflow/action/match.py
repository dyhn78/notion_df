from __future__ import annotations

import datetime as dt
import re
from abc import ABCMeta
from typing import Iterable, Optional, Any, Literal

from loguru import logger

from notion_df.core.request import Paginator
from notion_df.entity import Page, Database
from notion_df.object.filter import created_time_filter
from notion_df.object.rich_text import TextSpan, RichText
from notion_df.property import RelationProperty, TitleProperty, PageProperties, \
    DateFormulaPropertyKey, \
    DateProperty, CheckboxFormulaProperty, RichTextProperty, SelectProperty, \
    RelationPagePropertyValue
from notion_df.util.misc import repr_object
from workflow.block_enum import DatabaseEnum, SCHEDULE, START, PROGRESS
from workflow.core.action import SequentialAction, Action
from workflow.emoji_code import EmojiCode

korean_weekday = '월화수목금토일'

record_datetime_auto_prop = DateFormulaPropertyKey(EmojiCode.TIMER + '일시')
record_timestr_prop = RichTextProperty(EmojiCode.CALENDAR + '시간')
datei_to_weeki_prop = RelationProperty(DatabaseEnum.weeki_db.prefix_title)
datei_date_prop = DateProperty(EmojiCode.CALENDAR + '날짜')
weeki_date_range_prop = DateProperty(EmojiCode.BIG_CALENDAR + '날짜 범위')
event_title_prop = TitleProperty(EmojiCode.ORANGE_BOOK + '제목')
event_to_datei_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
event_to_stage_prop = RelationProperty(DatabaseEnum.thread_db.prefix_title)
event_to_point_prop = RelationProperty(DatabaseEnum.idea_db.prefix_title)
event_to_issue_prop = RelationProperty(DatabaseEnum.issue_db.prefix_title)
event_to_reading_prop = RelationProperty(DatabaseEnum.reading_db.prefix_title)
event_to_topic_prop = RelationProperty(DatabaseEnum.summit_db.prefix_title)
event_to_gist_prop = RelationProperty(DatabaseEnum.gist_db.prefix_title)
record_kind_prop = SelectProperty("📕유형")
record_kind_progress = "🌳진행"
reading_to_main_date_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
reading_to_start_date_prop = RelationProperty(DatabaseEnum.datei_db.prefix + START)
reading_to_event_prog_prop = RelationProperty(DatabaseEnum.event_db.prefix + PROGRESS)
reading_match_date_by_created_time_prop = CheckboxFormulaProperty(
    EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')
status_prop = SelectProperty("📘정리")
status_auto_generated = "⚙️자동"


# TODO
#  - 읽기 - 📕유형 <- 꼭지> 추가 (스펙 논의 필요)
#  - 일간/주간 1년 앞서 자동생성

class MatchActionBase:
    def __init__(self):
        self.date_namespace = DateINamespace()
        self.week_namespace = WeekINamespace()


class MatchAction(Action, metaclass=ABCMeta):
    def __init__(self, base: MatchActionBase):
        self.base = base
        self.date_namespace = base.date_namespace
        self.week_namespace = base.week_namespace


class MatchSequentialAction(MatchAction, SequentialAction, metaclass=ABCMeta):
    pass


WriteTitleT = Literal['if_datei_empty', 'if_separator_exists', 'never']


class MatchRecordDatei(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum,
                 record_to_datei: str, *,
                 read_datei_from_title: bool = False,
                 prepend_datei_on_title: bool = False,
                 only_if_separator_exists: bool = False,
                 ):
        """
        :arg read_datei_from_title: can get the datei from the record title if the current value includes "YYMMDD"
        :arg prepend_datei_on_title: prepend the date string "YYMMDD" to the record title
        """
        super().__init__(base)
        self.record_db = record.entity
        self.record_to_datei = RelationProperty(
            f'{DatabaseEnum.datei_db.prefix}{record_to_datei}')
        self.read_datei_from_title = read_datei_from_title
        self.prepend_datei_on_title = prepend_datei_on_title
        self.only_if_separator_exists = only_if_separator_exists

    def __repr__(self):
        return repr_object(self,
                           record_db_title=self.record_db.data.title,
                           record_to_datei=self.record_to_datei)

    def query(self) -> Paginator[Page]:
        return self.record_db.query(self.record_to_datei.filter.is_empty())

    def process_page(self, record: Page) -> None:
        if record.data.parent != self.record_db:
            return
        if record.data.properties[self.record_to_datei]:
            self.process_if_record_to_datei_not_empty(record)
        else:
            self.process_if_record_to_datei_empty(record)

    def process_if_record_to_datei_not_empty(self, record: Page) -> None:
        datei_list = record.data.properties[self.record_to_datei]
        for datei in datei_list:
            datei.get_data()
        if self.prepend_datei_on_title and (new_title := self.date_namespace.prepend_date_in_record_title(
                record.retrieve().data.properties.title, datei_list)):
            properties = PageProperties()
            properties[record.data.properties.title_prop] = new_title
            record.update(properties)
            logger.info(f'{record} -> {properties}')

    def process_if_record_to_datei_empty(self, record: Page) -> None:
        if self.only_if_separator_exists:
            title_plain_text = record.data.properties.title.plain_text
            if title_plain_text and '|' not in title_plain_text:
                return

        if (self.read_datei_from_title
                and (datei := self.date_namespace.get_page_by_record_title(
                    record.data.properties.title.plain_text)) is not None):
            self._update_page(record, PageProperties({
                self.record_to_datei: self.record_to_datei.page_value([datei]),
            }))
            return

        record_created_date = get_record_created_date(record)
        datei = self.date_namespace.get_page_by_date(record_created_date)
        properties: PageProperties[RelationPagePropertyValue | RichText] = \
            PageProperties({
                self.record_to_datei: self.record_to_datei.page_value([datei]),
            })
        if self.prepend_datei_on_title and (new_title := self.date_namespace.prepend_date_in_record_title(
                record.retrieve().data.properties.title, [datei])):
            properties[record.data.properties.title_prop] = new_title
        self._update_page(record, properties)

    def _update_page(self, record, record_properties: PageProperties) -> None:
        if not record_properties:
            return
        # final check if the property value is filled in the meantime
        if record.retrieve().data.properties[self.record_to_datei]:
            logger.info(f'{record} -> Skipped')
            return
        record.update(record_properties)
        logger.info(f'{record} -> {record_properties}')


class MatchRecordDateiSchedule(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum):
        super().__init__(base)
        self.record_db = record.entity
        self.record_to_datei_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
        self.record_to_datei_sch_prop = RelationProperty(f"{DatabaseEnum.datei_db.prefix}{SCHEDULE}")

    def __repr__(self):
        return repr_object(self, record_db=self.record_db)

    def query(self) -> Iterable[Page]:
        return self.record_db.query(self.record_to_datei_sch_prop.filter.is_not_empty())

    def process_page(self, record: Page) -> Any:
        if not (record.data.parent == self.record_db):
            return
        record_datei = record.data.properties[self.record_to_datei_prop]
        record_datei_new = record_datei + record.data.properties[self.record_to_datei_sch_prop]
        if record_datei == record_datei_new:
            logger.info(f'{record} : Skipped')
            return
        record.update(PageProperties({
            self.record_to_datei_prop: record_datei_new
        }))


class MatchReadingStartDatei(MatchSequentialAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.reading_db = DatabaseEnum.reading_db.entity
        self.event_db = DatabaseEnum.event_db.entity

    def query(self) -> Paginator[Page]:
        return self.reading_db.query(
            reading_to_start_date_prop.filter.is_empty() & (
                    reading_to_event_prog_prop.filter.is_not_empty()
                    | reading_to_main_date_prop.filter.is_not_empty()
                    | reading_match_date_by_created_time_prop.filter.is_not_empty()
            )
        )

    def process_page(self, reading: Page) -> None:
        if not (reading.data.parent == self.reading_db
                and not reading.data.properties[reading_to_start_date_prop]):
            return

        datei = self.find_datei(reading)
        if not datei:
            logger.info(f'{reading} : Skipped')
            return
        # final check if the property value is filled in the meantime
        if reading.retrieve().data.properties[reading_to_start_date_prop]:
            logger.info(f'{reading} : Skipped')
            return
        reading.update(PageProperties({
            reading_to_start_date_prop: reading_to_start_date_prop.page_value([datei])
        }))
        logger.info(f'{reading} - {reading_to_main_date_prop.name} : {datei}')

    def find_datei(self, reading: Page) -> Optional[Page]:
        def get_reading_event_dates() -> Iterable[Page]:
            reading_event_progs = reading.data.properties[reading_to_event_prog_prop]
            # TODO: RollupPagePropertyValue 구현 후 이곳을 간소화
            for event in reading_event_progs:
                if not (date_list := event.get_data().properties[event_to_datei_prop]):
                    continue
                date = date_list[0]
                if date.get_data().properties[datei_date_prop] is None:
                    continue
                yield date

        # ignore reading_main_date := reading.data.properties[reading_to_main_date_prop]
        if reading_event_dateis := {*get_reading_event_dates()}:
            return get_earliest_date(reading_event_dateis)
        if (datei_by_title := self.date_namespace.get_page_by_record_title(
                reading.data.properties.title.plain_text)) is not None:
            return datei_by_title
        if reading.data.properties[reading_match_date_by_created_time_prop]:
            reading_created_date = get_record_created_date(reading)
            return self.date_namespace.get_page_by_date(reading_created_date)


class MatchRecordTimestr(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum,
                 record_to_date: str):
        super().__init__(base)
        self.record_db = Database(record.id)
        self.record_to_datei = RelationProperty(
            DatabaseEnum.datei_db.prefix + record_to_date)

    def __repr__(self):
        return repr_object(self,
                           record_db=self.record_db,
                           record_to_datei=self.record_to_datei)

    def query(self) -> Iterable[Page]:
        # since the benefits are concentrated on near present days,
        # we could easily limit query() with today without lamentations
        return self.record_db.query(record_timestr_prop.filter.is_empty()
                                    & created_time_filter.equals(dt.date.today()))

    def will_process(self, record: Page) -> bool:
        if not (record.data.parent == self.record_db and not record.data.properties[
            record_timestr_prop]):
            return False
        try:
            record_date = record.data.properties[self.record_to_datei][0]
        except IndexError:
            return True
        record_date_range = record_date.data.properties[datei_date_prop]
        if record_date_range is None:
            return False
        record_date = record_date.data.properties[datei_date_prop].start
        return record.data.created_time.date() == record_date

    def process_page(self, record: Page) -> None:
        if not self.will_process(record):
            return
        timestr = record.data.created_time.strftime('%H:%M')
        if record.retrieve().data.properties[record_timestr_prop]:
            logger.info(f'{record} : Skipped')
            return
        record.update(PageProperties({
            record_timestr_prop: record_timestr_prop.page_value([TextSpan(timestr)])}))
        logger.info(f'{record} : {timestr}')


class MatchRecordWeekiByDatei(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record_db_enum: DatabaseEnum,
                 record_to_week: str, record_to_date: str):
        super().__init__(base)
        self.record_db = record_db_enum.entity
        self.record_db_title = self.record_db.data.title = record_db_enum.title
        self.record_to_weeki = RelationProperty(
            f'{DatabaseEnum.weeki_db.prefix}{record_to_week}')
        self.record_to_datei = RelationProperty(
            f'{DatabaseEnum.datei_db.prefix}{record_to_date}')

    def __repr__(self):
        return repr_object(self,
                           record_db_title=self.record_db_title,
                           record_to_weeki=self.record_to_weeki,
                           record_to_datei=self.record_to_datei)

    def query(self) -> Paginator[Page]:
        return self.record_db.query(
            self.record_to_weeki.filter.is_empty() & self.record_to_datei.filter.is_not_empty())

    def process_page(self, record: Page) -> None:
        if not (record.data.parent == self.record_db and record.data.properties[
            self.record_to_datei]):
            return

        new_record_weeks = self.record_to_weeki.page_value()
        for record_date in record.data.properties[self.record_to_datei]:
            if not record_date.data:
                record_date.retrieve()
            try:
                new_record_weeks.append(
                    record_date.data.properties[datei_to_weeki_prop][0])
            except IndexError:
                pass  # TODO: add warning

        # final check if the property value is filled or changed in the meantime
        prev_record_weeks = record.data.properties[self.record_to_weeki]
        if set(prev_record_weeks) == set(new_record_weeks):
            logger.info(f'{record} : Skipped')
            return

        curr_record_weeks = record.retrieve().data.properties[self.record_to_weeki]
        if ((set(prev_record_weeks) != set(curr_record_weeks))
                or (set(curr_record_weeks) == set(new_record_weeks))):
            logger.info(f'{record} : Skipped')
            return
        record.update(PageProperties({self.record_to_weeki: new_record_weeks}))
        logger.info(f'{record} : {list(new_record_weeks)}')
        return


class MatchDatei(MatchSequentialAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.date_db = DatabaseEnum.datei_db.entity

    def __repr__(self):
        return repr_object(self)

    def query(self) -> Paginator[Page]:
        return self.date_db.query(datei_date_prop.filter.is_empty()
                                  or datei_to_weeki_prop.filter.is_empty())

    def process_page(self, datei: Page) -> None:
        if not (datei.data.parent == self.date_db):
            return
        if not datei.data.properties[datei_date_prop]:
            self.match_date(datei)
        if not datei.data.properties[datei_to_weeki_prop]:
            self.match_weeki(datei)

    def match_date(self, datei: Page) -> None:
        date = self.date_namespace.get_date_of_title(
            datei.data.properties.title.plain_text)
        datei.update(PageProperties({datei_date_prop: datei_date_prop.page_value(start=date, end=None)}))
        logger.info(f'{datei} -> {date}')

    def match_weeki(self, datei: Page) -> None:
        date = datei.data.properties[datei_date_prop].start
        weeki = self.week_namespace.get_page_by_date(date)
        if datei.retrieve().data.properties[datei_to_weeki_prop]:
            return
        datei.update(
            PageProperties({datei_to_weeki_prop: datei_to_weeki_prop.page_value([weeki])}))
        logger.info(f'{datei} -> {weeki}')


class MatchEventProgress(MatchSequentialAction):
    event_db = DatabaseEnum.event_db.entity

    def __init__(self, base: MatchActionBase, target_db: DatabaseEnum):
        super().__init__(base)
        self.target_db = target_db
        self.event_to_target_prop = RelationProperty(target_db.prefix_title)
        self.event_to_target_prog_prop = RelationProperty(target_db.prefix + PROGRESS)

    def __repr__(self):
        return repr_object(self,
                           target_db=self.target_db)

    def query(self) -> Iterable[Page]:
        return self.event_db.query(
            filter=(self.event_to_target_prop.filter.is_not_empty()
                    & self.event_to_target_prog_prop.filter.is_empty()))

    def process_page(self, event: Page) -> Any:
        if event.data.parent != self.event_db:
            return
        self.process_page_forward(event)
        self.process_page_backward(event)

    def process_page_forward(self, event: Page) -> Any:
        if event.data.properties[self.event_to_target_prog_prop]:
            logger.info(
                f'{event} : Forward Skipped - {self.event_to_target_prog_prop.name} not empty')
            return
        if event.data.properties[status_prop] == status_auto_generated:
            logger.info(
                f'{event} : Forward Skipped - {status_prop.name} == {status_auto_generated}'
            )

        # TODO: more edge case handling
        if not (len(target_list := event.data.properties[
            self.event_to_target_prop]) == 1
                and sum([len(event.data.properties[prop]) for prop in [
                    event_to_topic_prop, event_to_gist_prop,
                    event_to_issue_prop, event_to_reading_prop,
                    event_to_stage_prop, event_to_point_prop
                ]]) == 1):
            logger.info(f'{event} : Forward Skipped')
            return
        event.update(properties=PageProperties({
            self.event_to_target_prog_prop: target_list
        }))

    def process_page_backward(self, event: Page) -> Any:
        event_readings = event.data.properties[self.event_to_target_prop]
        event_readings_new = event_readings + event.data.properties[
            self.event_to_target_prog_prop]
        if event_readings == event_readings_new:
            logger.info(f'{event} : Backward Skipped')
            return
        event.update(PageProperties({
            self.event_to_target_prop: event_readings_new
        }))


class DatabaseNamespace(metaclass=ABCMeta):
    def __init__(self, database: DatabaseEnum, title_prop: str):
        self.database = database.entity
        self.title_prop = TitleProperty(title_prop)
        self.pages_by_title_plain_text: dict[str, Page] = {}

    def get_page_by_title(self, title_plain_text: str) -> Optional[Page]:
        if page := self.pages_by_title_plain_text.get(title_plain_text):
            return page
        page_list = self.database.query(
            self.title_prop.filter.equals(title_plain_text))
        if not page_list:
            return
        page = page_list[0]
        self.pages_by_title_plain_text[page.data.properties.title.plain_text] = page
        return page


class DateINamespace(DatabaseNamespace):
    def __init__(self):
        super().__init__(DatabaseEnum.datei_db, EmojiCode.GREEN_BOOK + '제목')

    def get_page_by_date(self, date: dt.date) -> Page:
        day_name = korean_weekday[date.weekday()] + '요일'
        title_plain_text = f'{date.strftime("%y%m%d")} {day_name}'
        return self.get_page_by_title(title_plain_text) or self.create_page(
            title_plain_text, date)

    def get_page_by_record_title(self, title_plain_text: str) -> Optional[Page]:
        date = self.get_date_of_title(title_plain_text)
        if date is None:
            return
        return self.get_page_by_date(date)

    def create_page(self, title_plain_text: str, date: dt.date) -> Page:
        page = self.database.create_child_page(PageProperties({
            self.title_prop: self.title_prop.page_value.from_plain_text(
                title_plain_text),
            datei_date_prop: datei_date_prop.page_value(start=date, end=None)
        }))
        self.pages_by_title_plain_text[page.data.properties.title.plain_text] = page
        return page

    _getter_pattern = re.compile(r'(\d{2})(\d{2})(\d{2}).*')
    _getter_pattern_2 = re.compile(r'(\d{2})(\d{2})(\d{2})[|]')
    _checker_pattern = _getter_pattern

    @classmethod
    def strf_date(cls, datei: Page) -> str:
        return datei.data.properties[datei_date_prop].start.strftime("%y%m%d")

    @classmethod
    def get_date_of_title(cls, title_plain_text: str) -> Optional[dt.date]:
        match = cls._getter_pattern.match(
            title_plain_text) or cls._getter_pattern_2.search(title_plain_text)
        return cls._parse_date_match(match)

    @classmethod
    def _check_date_in_record_title(cls, title_plain_text: str, dates: list[dt.date]) -> bool:
        match = cls._checker_pattern.search(title_plain_text)
        date_in_record_title = cls._parse_date_match(match)
        return date_in_record_title in dates

    @classmethod
    def _parse_date_match(cls, match: Optional[re.Match[str]]) -> Optional[dt.date]:
        if not match:
            return None
        year, month, day = (int(s) for s in match.groups())
        full_year = (2000 if year < 90 else 1900) + year
        try:
            return dt.date(full_year, month, day)
        except ValueError:
            # In case the date is not valid (like '000229' for non-leap year)
            return None

    _digit_pattern = re.compile(r'[\d. -]+')

    @classmethod
    def prepend_date_in_record_title(
            cls, title: RichText, datei_list: Iterable[Page]
    ) -> RichText:
        datei_date_list = [datei.data.properties[datei_date_prop].start for datei in datei_list]

        needs_update = not cls._check_date_in_record_title(title.plain_text, datei_date_list)
        if not needs_update:
            return RichText()

        earliest_datei_date = min(datei_date_list)
        has_separator = '|' in title.plain_text
        needs_separator: bool = not has_separator  # and cls._digit_pattern.match(title.plain_text))
        starts_with_separator = title.plain_text.startswith('|')
        return RichText([TextSpan(
            f"{earliest_datei_date.strftime('%y%m%d')}{'|' if needs_separator else ''}"
            f"{'' if starts_with_separator else ' '}"
            f"{'✨' if not title.plain_text else ''}"),
            *title])


class WeekINamespace(DatabaseNamespace):
    def __init__(self):
        super().__init__(DatabaseEnum.weeki_db, EmojiCode.GREEN_BOOK + '제목')

    def get_page_by_date(self, date: dt.date) -> Page:
        title_plain_text = self._get_first_day_of_week(date).strftime("%y/%U")
        return self.get_page_by_title(title_plain_text) or self.create_page(
            title_plain_text, date)

    def create_page(self, title_plain_text: str, date: dt.date) -> Page:
        page = self.database.create_child_page(PageProperties({
            self.title_prop: self.title_prop.page_value.from_plain_text(
                title_plain_text),
            weeki_date_range_prop: weeki_date_range_prop.page_value(
                start=self._get_first_day_of_week(date),
                end=self._get_last_day_of_week(date))
        }))
        self.pages_by_title_plain_text[page.data.properties.title.plain_text] = page
        return page

    @classmethod
    def _get_first_day_of_week(cls, date: dt.date) -> dt.date:
        # returns the first day (sunday) of the week.
        weekday = (date.weekday() + 1) % 7
        return date + dt.timedelta(days=-weekday)

    @classmethod
    def _get_last_day_of_week(cls, date: dt.date) -> dt.date:
        return cls._get_first_day_of_week(date) + dt.timedelta(days=6)


def get_record_created_date(record: Page) -> dt.date:
    # TODO: '📆일시' parsing 지원
    return (record.get_data().created_time + dt.timedelta(hours=-5)).date()


def get_earliest_date(datei_it: Iterable[Page]) -> Page:
    """only works for children of `DatabaseEnum.datei_db` or `weeki_db`"""

    def _get_start_date(datei: Page) -> dt.date:
        parent_db = DatabaseEnum.from_entity(datei.get_data().parent)
        if parent_db == DatabaseEnum.datei_db:
            prop = datei_date_prop
        elif parent_db == DatabaseEnum.weeki_db:
            prop = weeki_date_range_prop
        else:
            raise ValueError(datei)
        return datei.get_data().properties[prop].start

    return min(datei_it, key=_get_start_date)

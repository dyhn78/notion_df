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
from notion_df.property import RelationProperty, TitleProperty, PageProperties, \
    DateFormulaPropertyKey, \
    DateProperty, CheckboxFormulaProperty, RichTextProperty, SelectProperty, \
    RelationPagePropertyValue
from notion_df.util.misc import repr_object
from workflow.block_enum import DatabaseEnum
from workflow.core.action import SequentialAction, Action
from workflow.emoji_code import EmojiCode

korean_weekday = '월화수목금토일'
record_datetime_auto_prop = DateFormulaPropertyKey(EmojiCode.TIMER + '일시')
record_timestr_prop = RichTextProperty(EmojiCode.CALENDAR + '시간')
datei_to_week_prop = RelationProperty(DatabaseEnum.weeki_db.prefix_title)
datei_date_prop = DateProperty(EmojiCode.CALENDAR + '날짜')
weeki_date_range_prop = DateProperty(EmojiCode.BIG_CALENDAR + '날짜 범위')
event_title_prop = TitleProperty(EmojiCode.ORANGE_BOOK + '제목')
event_to_datei_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
event_to_stage_prop = RelationProperty(DatabaseEnum.stage_db.prefix_title)
event_to_point_prop = RelationProperty(DatabaseEnum.point_db.prefix_title)
event_to_issue_prop = RelationProperty(DatabaseEnum.issue_db.prefix_title)
event_to_reading_prop = RelationProperty(DatabaseEnum.reading_db.prefix_title)
event_to_topic_prop = RelationProperty(DatabaseEnum.topic_db.prefix_title)
event_to_gist_prop = RelationProperty(DatabaseEnum.gist_db.prefix_title)
topic_base_type_prop = SelectProperty("📕유형")
topic_base_type_progress = "🌳진행"
reading_to_main_date_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
reading_to_start_date_prop = RelationProperty(DatabaseEnum.datei_db.prefix + '시작')
reading_to_event_prog_prop = RelationProperty(DatabaseEnum.event_db.prefix + '진도')
reading_match_date_by_created_time_prop = CheckboxFormulaProperty(
    EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')


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


class MatchDatei(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum,
                 record_to_datei: str, *,
                 read_title: bool = False, write_title: bool = False):
        """
        :arg read_title: can get the datei from the record title if the current value includes "YYMMDD"
        :arg write_title: prepend the date string "YYMMDD" to the record title, unless its current value includes "YY"
        """
        super().__init__(base)
        self.record_db = record.entity
        self.record_to_datei = RelationProperty(
            f'{DatabaseEnum.datei_db.prefix}{record_to_datei}')
        self.read_title = read_title
        self.write_title = write_title

    def __repr__(self):
        return repr_object(self,
                           record_db=self.record_db,
                           record_to_date=self.record_to_datei)

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
        datei = record.data.properties[self.record_to_datei][0]
        datei.get_data()
        if (self.write_title
                and (new_title := self.date_namespace.format_record_title(
                    record.data.properties.title, datei))):
            properties = PageProperties()
            properties[record.data.properties.title_prop] = new_title
            record.update(properties)
            logger.info(f'{record} -> {properties}')

    def process_if_record_to_datei_empty(self, record: Page) -> None:
        if (self.read_title
                and (datei := self.date_namespace.get_datei_by_record_title(
                    record.data.properties.title.plain_text)) is not None):
            self._update_page(record, PageProperties({
                self.record_to_datei: self.record_to_datei.page_value([datei]),
            }))
            return

        record_created_date = get_record_created_date(record)
        datei = self.date_namespace.get_datei_by_date(record_created_date)
        properties: PageProperties[RelationPagePropertyValue | RichText] = \
            PageProperties({
                self.record_to_datei: self.record_to_datei.page_value([datei]),
            })
        if (self.write_title
                and (new_title := self.date_namespace.format_record_title(
                    record.data.properties.title, datei))):
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


class MatchReadingDatei(MatchSequentialAction):
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

        if reading_event_and_main_dates := {*get_reading_event_dates(),
                                            *reading.data.properties[
                                                reading_to_main_date_prop]}:
            return get_earliest_date(reading_event_and_main_dates)
        if (datei_by_title := self.date_namespace.get_datei_by_record_title(
                    record.data.properties.title.plain_text)) is not None:
            return datei_by_title
        if reading.data.properties[reading_match_date_by_created_time_prop]:
            reading_created_date = get_record_created_date(reading)
            return self.date_namespace.get_datei_by_date(reading_created_date)

class MatchTimestr(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum,
                 record_to_date: str):
        super().__init__(base)
        self.record_db = Database(record.id)
        self.record_to_date = RelationProperty(
            DatabaseEnum.datei_db.prefix + record_to_date)

    def query(self) -> Iterable[Page]:
        # since the benefits are concentrated on near present days,
        # we could easily limit query() with today without lamentations
        return self.record_db.query(record_timestr_prop.filter.is_empty()
                                    & created_time_filter.equals(dt.date.today()))

    def filter(self, record: Page) -> bool:
        if not (record.data.parent == self.record_db and not record.data.properties[
            record_timestr_prop]):
            return False
        try:
            record_date = record.data.properties[self.record_to_date][0]
        except IndexError:
            return True
        record_date = record_date.data.properties[datei_date_prop].start
        return record.data.created_time.date() == record_date

    def process_page(self, record: Page) -> None:
        if not self.filter(record):
            return
        timestr = record.data.created_time.strftime('%H:%M')
        if record.retrieve().data.properties[record_timestr_prop]:
            logger.info(f'{record} : Skipped')
            return
        record.update(PageProperties({
            record_timestr_prop: record_timestr_prop.page_value([TextSpan(timestr)])}))
        logger.info(f'{record} : {timestr}')


class MatchWeekiByRefDate(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record_db_enum: DatabaseEnum,
                 record_to_week: str, record_to_date: str):
        super().__init__(base)
        self.record_db = record_db_enum.entity
        self.record_db_title = self.record_db.data.title = record_db_enum.title
        self.record_to_week = RelationProperty(
            f'{DatabaseEnum.weeki_db.prefix}{record_to_week}')
        self.record_to_date = RelationProperty(
            f'{DatabaseEnum.datei_db.prefix}{record_to_date}')

    def __repr__(self):
        return repr_object(self,
                           record_db_title=self.record_db_title,
                           record_to_week=self.record_to_week,
                           record_to_date=self.record_to_date)

    def query(self) -> Paginator[Page]:
        return self.record_db.query(
            self.record_to_week.filter.is_empty() & self.record_to_date.filter.is_not_empty())

    def process_page(self, record: Page) -> None:
        if not (record.data.parent == self.record_db and record.data.properties[
            self.record_to_date]):
            return

        new_record_weeks = self.record_to_week.page_value()
        for record_date in record.data.properties[self.record_to_date]:
            if not record_date.data:
                record_date.retrieve()
            new_record_weeks.append(record_date.data.properties[datei_to_week_prop][0])

        # final check if the property value is filled or changed in the meantime
        prev_record_weeks = record.data.properties[self.record_to_week]
        if set(prev_record_weeks) == set(new_record_weeks):
            logger.info(f'{record} : Skipped')
            return

        curr_record_weeks = record.retrieve().data.properties[self.record_to_week]
        if ((set(prev_record_weeks) != set(curr_record_weeks))
                or (set(curr_record_weeks) == set(new_record_weeks))):
            logger.info(f'{record} : Skipped')
            return
        record.update(PageProperties({self.record_to_week: new_record_weeks}))
        logger.info(f'{record} : {list(new_record_weeks)}')
        return


class MatchWeekiByDateValue(MatchSequentialAction):
    def __init__(self, base: MatchActionBase):
        super().__init__(base)
        self.date_db = DatabaseEnum.datei_db.entity

    def __repr__(self):
        return repr_object(self)

    def query(self) -> Paginator[Page]:
        return self.date_db.query(datei_to_week_prop.filter.is_empty())

    def process_page(self, datei: Page) -> None:
        if not (datei.data.parent == self.date_db and not datei.data.properties[
            datei_to_week_prop]):
            return

        date = datei.data.properties[datei_date_prop]
        if not date:
            logger.info(f'{datei} -> Skipped')
            return
        week = self.week_namespace.by_date(date.start)
        if datei.retrieve().data.properties[datei_to_week_prop]:
            return
        datei.update(
            PageProperties({datei_to_week_prop: datei_to_week_prop.page_value([week])}))
        logger.info(f'{datei} -> {week}')


class MatchEventProgress(MatchSequentialAction):
    event_db = DatabaseEnum.event_db.entity

    def __init__(self, base: MatchActionBase, target_db: DatabaseEnum):
        super().__init__(base)
        self.event_to_target_prop = RelationProperty(target_db.prefix_title)
        self.event_to_target_prog_prop = RelationProperty(target_db.prefix + '진도')

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
                f'{event} : Skipped - {self.event_to_target_prog_prop.name} not empty')
            return

        # TODO: more edge case handling
        if not (len(target_list := event.data.properties[
            self.event_to_target_prop]) == 1
                and sum([len(event.data.properties[prop]) for prop in [
                    event_to_topic_prop, event_to_gist_prop,
                    event_to_issue_prop, event_to_reading_prop,
                    event_to_stage_prop, event_to_point_prop
                ]]) == 1):
            logger.info(f'{event} : Skipped')
            return
        event.update(properties=PageProperties({
            self.event_to_target_prog_prop: target_list
        }))

    def process_page_backward(self, event: Page) -> Any:
        event_readings = event.data.properties[self.event_to_target_prop]
        event_readings_new = event_readings + event.data.properties[
            self.event_to_target_prog_prop]
        if event_readings == event_readings_new:
            logger.info(f'{event} : Skipped')
            return
        event.update(PageProperties({
            self.event_to_target_prop: event_readings_new
        }))


class CreateProgressEvent(MatchSequentialAction):
    event_db = DatabaseEnum.event_db.entity
    target_to_datei_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
    target_to_event_prop = RelationProperty(DatabaseEnum.event_db.prefix_title)
    target_to_event_prog_prop = RelationProperty(DatabaseEnum.event_db.prefix + '진도')

    def __init__(self, base: MatchActionBase, target_db: DatabaseEnum):
        super().__init__(base)
        self.target_db = target_db.entity
        self.event_to_target_prog_prop = RelationProperty(target_db.prefix + '진도')
        self.event_to_target_prop = RelationProperty(target_db.prefix_title)

    def query(self) -> Iterable[Page]:
        return self.target_db.query(
            filter=self.target_to_datei_prop.filter.is_not_empty())

    def process_page(self, target: Page) -> Any:
        if target.data.parent != self.target_db:
            return
        datei_list = target.data.properties[self.target_to_datei_prop]
        datei_without_event_list = set(datei_list)
        for event in target.data.properties[self.target_to_event_prop]:
            for datei in event.get_data().properties[event_to_datei_prop]:
                datei_without_event_list.discard(datei)
        logger.info(f'{target=}, {datei_without_event_list=}')

        for datei in datei_without_event_list:
            event = self.event_db.create_child_page(PageProperties({
                self.event_to_target_prop: self.event_to_target_prop.page_value([target]),
                self.event_to_target_prog_prop: self.event_to_target_prog_prop.page_value([target]),
                event_to_datei_prop: event_to_datei_prop.page_value([datei]),
                event_title_prop: event_title_prop.page_value.from_plain_text(
                    self.date_namespace.strf_date(datei))
            }))
            logger.info(f'{target=}, {event=}')


class DeprMatchTopic(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum, ref: DatabaseEnum,
                 record_to_ref_prop_name: str, record_to_topic_prop_name: str,
                 ref_to_topic_prop_name: str):
        super().__init__(base)
        self.record_db = record.entity
        self.ref_db = ref.entity
        self.record_to_ref_prop = RelationProperty(record_to_ref_prop_name)
        self.record_to_topic_prop = RelationProperty(record_to_topic_prop_name)
        self.ref_to_topic_prop = RelationProperty(ref_to_topic_prop_name)

    def query(self) -> Iterable[Page]:
        return self.record_db.query(self.record_to_ref_prop.filter.is_not_empty())

    def process_page(self, record: Page) -> None:
        if not (record.data.parent == self.record_db
                and record.data.properties[self.record_to_ref_prop]):
            return

        # TODO: rewrite so that it utilizes the RelationPagePropertyValue's feature
        #  (rather than based on builtin list and set)
        curr_topic_list: list[Page] = list(
            record.data.properties[self.record_to_topic_prop])
        new_topic_set: set[Page] = set(curr_topic_list)
        for ref in record.data.properties[self.record_to_ref_prop]:
            ref_topic_set = {topic for topic in
                             ref.get_data().properties[self.ref_to_topic_prop]
                             if topic.get_data().properties[
                                 topic_base_type_prop] == topic_base_type_progress}
            if set(curr_topic_list) & ref_topic_set:
                continue
            new_topic_set.update(ref_topic_set)
        if not new_topic_set - set(curr_topic_list):
            return
        curr_topic_list = list(
            record.retrieve().data.properties[self.record_to_topic_prop])
        new_topic = curr_topic_list + list(new_topic_set)
        record.update(PageProperties({
            self.record_to_topic_prop: self.record_to_topic_prop.page_value(
                new_topic)}))


class DatabaseNamespace(metaclass=ABCMeta):
    def __init__(self, database: DatabaseEnum, title_prop: str):
        self.database = database.entity
        self.title_prop = TitleProperty(title_prop)
        self.pages_by_title_plain_text: dict[str, Page] = {}

    def by_title(self, title_plain_text: str) -> Page:
        if not (page := self.pages_by_title_plain_text.get(title_plain_text)):
            date_list = self.database.query(
                self.title_prop.filter.equals(title_plain_text))
            if date_list:
                page = date_list[0]
            else:
                page = self.database.create_child_page(PageProperties({
                    self.title_prop: self.title_prop.page_value.from_plain_text(
                        title_plain_text)
                }))
            self.pages_by_title_plain_text[page.data.properties.title.plain_text] = page
        return page


class DateINamespace(DatabaseNamespace):
    def __init__(self):
        super().__init__(DatabaseEnum.datei_db, EmojiCode.GREEN_BOOK + '제목')

    @classmethod
    def strf_date(cls, datei: Page) -> str:
        return datei.data.properties[datei_date_prop].start.strftime("%y%m%d")

    def get_datei_by_date(self, date: dt.date) -> Page:
        day_name = korean_weekday[date.weekday()] + '요일'
        title_plain_text = f'{date.strftime("%y%m%d")} {day_name}'
        return self.by_title(title_plain_text)

    def get_datei_by_record_title(self, title_plain_text: str) -> Optional[Page]:
        date = self._get_date_from_record_title(title_plain_text)
        if date is None:
            return
        return self.get_datei_by_date(date)

    _getter_pattern = re.compile(r'(\d{2})(\d{2})(\d{2}).*')
    _getter_pattern_2 = re.compile(r'(\d{2})(\d{2})(\d{2})|')

    @classmethod
    def _get_date_from_record_title(cls, title_plain_text: str) -> Optional[dt.date]:
        match = cls._getter_pattern.match(title_plain_text) or cls._getter_pattern_2.search(title_plain_text) 
        if not match:
            return None
        year, month, day = (int(s) for s in match.groups())
        if year > 90:  # TODO
            return None
        try:
            return dt.date(2000 + year, month, day)
        except ValueError:
            # In case the date is not valid (like '000229' for non-leap year)
            return None

    _checker_pattern = re.compile(r'(\d{2}).*')
    _digit_pattern = re.compile(r'[\d. -]+')

    @classmethod
    def format_record_title(cls, title: RichText, datei: Page) -> RichText:
        if cls._checker_pattern.search(title.plain_text):
            return RichText()
        date = datei.data.properties[datei_date_prop].start
        needs_separator: bool = ('|' not in title.plain_text) and not cls._digit_pattern.match(title.plain_text)
        return RichText([TextSpan(
            f"{date.strftime('%y%m%d')}{'|' if needs_separator else ''} "),
            *title])


class WeekINamespace(DatabaseNamespace):
    def __init__(self):
        super().__init__(DatabaseEnum.weeki_db, EmojiCode.GREEN_BOOK + '제목')

    def by_date(self, date: dt.date) -> Page:
        title_plain_text = self.get_first_day_of_week(date).strftime("%y/%U")
        return self.by_title(title_plain_text)

    @classmethod
    def get_first_day_of_week(cls, date: dt.date) -> dt.date:
        # returns the first day (sunday) of the week.
        weekday = (date.weekday() + 1) % 7
        return date + dt.timedelta(days=-weekday)

    @classmethod
    def get_last_day_of_week(cls, date: dt.date) -> dt.date:
        return cls.get_first_day_of_week(date) + dt.timedelta(days=6)


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

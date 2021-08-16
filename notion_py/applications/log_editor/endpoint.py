# from pprint import pprint
from notion_py.applications.constants import \
    ID_PERIODS, ID_DATES, ID_JOURNALS, ID_SHOTS, ID_WRITINGS, ID_MEMOS
from notion_py.gateway.parse import PageListParser
from notion_py.gateway.query import Query
from notion_py.utility.stopwatch import stopwatch
from notion_py.applications.log_editor.match_property import MatchbyReference, \
    MatchorCreatebyIndex
from notion_py.applications.log_editor.date_to_period import NaljjaToGigan
from .constants import *


def update_dates(check_only_past_x_days=0):
    editor = LogEditor(TO_DATES, DOMAINS_INDEX,
                       check_only_past_x_days=check_only_past_x_days)
    dates = editor.query_parents(ID_DATES, DATES_INDEX)
    journals = editor.query_parents(ID_JOURNALS, DOMAINS_INDEX)
    request = MatchorCreatebyIndex.default(
        journals, dates, ID_DATES, TO_DATES,
        DOMAINS_INDEX, TITLE_PROPERTY, as_naljja
    )
    stopwatch('일지->날짜')
    request.execute()

    memos = editor.query_children(ID_MEMOS)
    request = MatchorCreatebyIndex.default(
        memos, dates, ID_DATES, TO_DATES,
        DOMAINS_INDEX, TITLE_PROPERTY, as_naljja
    )
    stopwatch('메모->날짜')
    request.execute()

    def match_children(children_id: str, children_name: str):
        children = editor.query_children(children_id)
        first_request = MatchbyReference.default(
            children, journals, TO_DATES, TO_JOURNALS, TO_DATES
        )
        stopwatch(f'{children_name}-(일지)->날짜')
        children = first_request.execute(reprocess_outside=True)
        second_request = MatchorCreatebyIndex.default(
            children, dates, ID_DATES, TO_DATES,
            DOMAINS_INDEX, TITLE_PROPERTY, as_naljja
        )
        stopwatch(f'{children_name}-(x)->날짜')
        second_request.execute()

    match_children(ID_SHOTS, '진도')
    match_children(ID_WRITINGS, '쓰기')


def update_periods(check_only_past_x_days=0):
    editor = LogEditor(TO_PERIODS, DOMAINS_INDEX,
                       check_only_past_x_days=check_only_past_x_days)
    periods = editor.query_parents(ID_PERIODS, PERIODS_INDEX)
    dates = editor.query_parents(ID_DATES, DATES_INDEX)
    request = NaljjaToGigan(dates, periods)
    stopwatch('날짜->기간')
    request.execute()

    def match_children(children_id: str, children_name: str):
        children = editor.query_children(children_id)
        match_request = MatchbyReference.default(
            children, dates, TO_PERIODS, TO_DATES, TO_PERIODS
        )
        stopwatch(f'{children_name}-(날짜)->기간')
        match_request.execute()

    match_children(ID_JOURNALS, '일지')
    match_children(ID_SHOTS, '진도')
    match_children(ID_WRITINGS, '쓰기')
    match_children(ID_MEMOS, '메모')


class LogEditor:
    def __init__(self, domain_to_target: str, domain_date_index: str,
                 check_only_past_x_days: int):
        self.domain_to_target = domain_to_target
        self.domain_date_index = domain_date_index
        self.check_only_past_x_days = check_only_past_x_days

    def query_parents(self, page_id: str, date_index: str) -> PageListParser:
        query = Query(page_id)
        if self.check_only_past_x_days:
            frame = query.filter_maker.by_date(date_index)
            if self.check_only_past_x_days == 7:
                query.push_filter(frame.within_past_week())
            if self.check_only_past_x_days == 30:
                query.push_filter(frame.within_past_month())
        response = query.execute()
        page_list = PageListParser.from_query_response(response)
        return page_list

    def query_children(self, page_id: str) -> PageListParser:
        query = Query(page_id)
        frame = query.filter_maker.by_relation(self.domain_to_target)
        ft = frame.is_empty()
        if self.check_only_past_x_days:
            frame = query.filter_maker.by_date(self.domain_date_index)
            if self.check_only_past_x_days == 7:
                ft &= frame.within_past_week()
            elif self.check_only_past_x_days == 30:
                ft &= frame.within_past_month()
            elif self.check_only_past_x_days == 365:
                ft &= frame.within_past_year()
        query.push_filter(ft)
        response = query.execute()
        page_list = PageListParser.from_query_response(response)
        return page_list

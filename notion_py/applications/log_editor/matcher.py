from __future__ import annotations

from collections import Callable
from typing import Optional

from .time_property import ProcessTimeProperty
from ..page_ids import DatabaseInfo
from ...interface import RootEditor, TypeName


TITLE = '📚제목'
MANUAL_DATE_RANGE = '📅날짜 범위'
MANUAL_DATE = '📆날짜'
AUTO_DATE = '날짜값⏲️'

TO_PERIOD = '🧶기간'
TO_DATE = '🧶날짜'
TO_JOURNAL = '🧵일지'
TO_SHOT = '🧵진도'


class DateMatcher:
    def __init__(self, date_range=0):
        self.root = RootEditor()
        self.date_range = date_range

    def execute(self):
        periods = MatchBase(self, DatabaseInfo.PERIODS, index_as_target=TITLE,
                            index_as_domain=MANUAL_DATE_RANGE)
        dates = MatchBase(self, DatabaseInfo.DATES, index_as_target=TITLE,
                          index_as_domain=MANUAL_DATE)
        journals = MatchBase(self, DatabaseInfo.JOURNALS, index_as_domain=AUTO_DATE)
        memos = MatchBase(self, DatabaseInfo.MEMOS, index_as_domain=AUTO_DATE)
        shots = MatchBase(self, DatabaseInfo.SHOTS, index_as_domain=AUTO_DATE)
        writings = MatchBase(self, DatabaseInfo.WRITINGS, index_as_domain=AUTO_DATE)

        for matchbase in [periods, dates, journals, shots]:
            matchbase.query_as_parents()
        for matchbase in [memos, writings]:
            matchbase.query_as_children(dom_to_tar=TO_DATE)

        MatcherAlgorithm(journals, dates).match_by_index_then_create(
            TO_DATE, DateProcess.get_datepage_title, tar_writer_func=None
        )
        for matchbase in [shots, memos, writings]:
            MatcherAlgorithm(matchbase, dates, journals).match_by_ref_index_then_create(
                TO_DATE, TO_JOURNAL, TO_DATE,
                DateProcess.get_datepage_title, tar_writer_func=None
            )

        MatcherAlgorithm(dates, periods).match_by_index_then_create(
            TO_PERIOD, DateProcess.get_periodpage_title,
            DateProcess.get_writer_of_periodpage_for_daterange(MANUAL_DATE_RANGE)
        )
        for matchbase in [journals, shots, memos, writings]:
            MatcherAlgorithm(matchbase, periods, dates).match_by_ref(
                TO_PERIOD, TO_DATE, TO_PERIOD)

        for matchbase in [periods, dates, journals, memos, shots, writings]:
            matchbase.execute()


class DateProcess:
    @staticmethod
    def get_datepage_title(date: TypeName.date_format):
        return ProcessTimeProperty(date.start, plain_date=True).strf_dig6_and_weekday()

    @staticmethod
    def get_periodpage_title(date: TypeName.date_format):
        base = ProcessTimeProperty(date.start, plain_date=True)
        return base.strf_year_and_week()

    @staticmethod
    def get_writer_of_periodpage_for_daterange(prop_name):
        def wrapper(page: TypeName.tabular_page, index_value: TypeName.date_format):
            base = ProcessTimeProperty(index_value.start, plain_date=True)
            daterange = TypeName.date_format(
                start_date=base.first_day_of_week(),
                end_date=base.last_day_of_week()
            )
            page.props.write_date(prop_name, daterange)

        return wrapper


class MatcherAlgorithm:
    def __init__(self, domain: MatchBase,
                 target: MatchBase,
                 reference: MatchBase = None):
        self.domain = domain
        self.target = target
        self.reference = reference
        self.dom_index = self.domain.index_as_domain
        self.tar_index = self.target.index_as_target
        self.index_func: Optional[Callable] = None
        self.tars_by_index: dict[str, TypeName.tabular_page] = {}
        self.dom_to_tar = ''
        self.dom_to_ref = ''
        self.ref_to_tar = ''

    def match_by_ref(self, dom_to_tar, dom_to_ref, ref_to_tar):
        self.dom_to_tar = dom_to_tar
        self.dom_to_ref = dom_to_ref
        self.ref_to_tar = ref_to_tar
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            self._try_matching_by_ref(dom)

    def match_by_index(self, dom_to_tar, index_func: Callable):
        self.dom_to_tar = dom_to_tar
        self.index_func = index_func
        self.tars_by_index = self.target.pagelist.by_index(self.tar_index)
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            self._try_matching_by_index(dom)

    def match_by_ref_then_index(self, dom_to_tar, dom_to_ref, ref_to_tar,
                                index_func: Callable):
        self.match_by_ref(dom_to_tar, dom_to_ref, ref_to_tar)
        self.match_by_index(dom_to_tar, index_func)

    def match_by_index_then_create(
            self, dom_to_tar, index_func: Callable,
            tar_writer_func: Optional[Callable] = None):
        self.dom_to_tar = dom_to_tar
        self.index_func = index_func
        self.tars_by_index = self.target.pagelist.by_index(self.tar_index)
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            if result := self._try_matching_by_index_then_create_counterpart(dom):
                tar, tar_index_value = result
                if tar_writer_func is not None:
                    tar_writer_func(tar, tar_index_value)
        self.target.execute()
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            self._try_matching_by_index(dom)

    def match_by_ref_index_then_create(
            self, dom_to_tar, dom_to_ref, ref_to_tar,
            index_func: Callable, tar_writer_func: Optional[Callable] = None):
        self.match_by_ref(dom_to_tar, dom_to_ref, ref_to_tar)
        self.match_by_index_then_create(dom_to_tar, index_func, tar_writer_func)

    def _is_already_matched(self, dom: TypeName.tabular_page):
        return bool(dom.props.read_of(self.dom_to_tar))

    def _try_matching_by_ref(self, dom: TypeName.tabular_page):
        """
        will return False if matching is done;
        will return True or some non-empty information to put to next algorithm.
        """
        ref_ids = dom.props.read_of(self.dom_to_ref)
        for ref_id in ref_ids:
            if ref_id in self.reference.pagelist.keys():
                break
        else:
            return True
        ref = self.reference.pagelist.by_id[ref_id]
        tar_ids = ref.props.read_of(self.ref_to_tar)
        for tar_id in tar_ids:
            if tar_id in self.target.pagelist.keys():
                break
        else:
            return True
        dom.props.write(self.dom_to_tar, [tar_id])

    def _try_matching_by_index(self, dom: TypeName.tabular_page):
        dom_index_value = dom.props.read_of(self.dom_index)
        tar_index_value = self.index_func(dom_index_value)
        if tar_index_value not in self.tars_by_index.keys():
            return tar_index_value
        tar = self.tars_by_index[tar_index_value]
        tar_id = tar.master_id
        dom.props.write(self.dom_to_tar, [tar_id])

    def _try_matching_by_index_then_create_counterpart(
            self, dom: TypeName.tabular_page):
        if not (tar_index_value := self._try_matching_by_index(dom)):
            return False
        tar = self.target.pagelist.new_tabular_page()
        tar.props.write(self.tar_index, tar_index_value)
        return [tar, tar_index_value]


class MatchBase:
    def __init__(self, caller: DateMatcher, database_info: tuple,
                 index_as_target='', index_as_domain=''):
        self.index_as_target = index_as_target
        self.index_as_domain = index_as_domain

        self.caller = caller
        self.root = self.caller.root
        self.date_range = self.caller.date_range
        self.database = self.root.open_database(*database_info)
        self.pagelist = self.database.pagelist
        self.gateway: TypeName.query = self.pagelist.query_form

    def __iter__(self):
        return iter(self.pagelist.values())

    def execute(self):
        self.database.execute()

    def query_as_parents(self):
        if self.date_range:
            frame = self.gateway.make_filter.date_of(self.index_as_domain)
            if self.date_range == 7:
                self.gateway.push_filter(frame.within_past_week())
            if self.date_range == 30:
                self.gateway.push_filter(frame.within_past_month())
        self.pagelist.run_query()

    def query_as_children(self, dom_to_tar):
        frame = self.gateway.make_filter.relation_of(dom_to_tar)
        ft = frame.is_empty()
        if self.date_range:
            frame = self.gateway.make_filter.date_of(self.index_as_domain)
            if self.date_range == 7:
                ft &= frame.within_past_week()
            elif self.date_range == 30:
                ft &= frame.within_past_month()
            elif self.date_range == 365:
                ft &= frame.within_past_year()
        self.gateway.push_filter(ft)
        self.pagelist.run_query()

import datetime as dt
from abc import ABCMeta
from typing import Optional, Union

from notion_zap.cli.editors import PageRow, Database
from notion_zap.cli.structs import DateObject
from .periods import PeriodResetter
from ..common.date_handler import DateHandler
from ..common.dt_handler import TimeStringHandler
from ..common.helpers import (
    query_unique_page_by_idx,
    fetch_all_pages_of_relation, fetch_unique_page_of_relation
)
from ..common.struct import EditorManager


class DateMatcherAbs(EditorManager, metaclass=ABCMeta):
    Tdoms_ref = 'to_journals'
    Tdoms_date = 'auto_datetime'
    T_tar = 'to_dates'
    Ttars_idx = 'title'
    Ttars_date = 'manual_date'

    def __init__(self, bs):
        super().__init__(bs)
        self.target: Database = self.bs.dates
        self.reference = self.bs.journals
        self.target_by_idx = self.target.rows.index_by_tag(self.Ttars_idx)

    def determine_tar_from_auto_date(self, dom: PageRow):
        dom_idx: DateObject = dom.props.read_tag(self.Tdoms_date)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_tar_by_date(date_val)

    def find_or_create_tar_by_date(self, date_val: Union[dt.datetime, dt.date]):
        if tar := self.find_tar_by_date(date_val):
            return tar
        return self.create_tar_by_date(date_val)

    def find_tar_by_date(self, date_val: Union[dt.datetime, dt.date]):
        date_handler = DateHandler(date_val)
        tar_idx = date_handler.strf_dig6_and_weekday()
        if tar := self.target_by_idx.get(tar_idx):
            return tar
        if tar := query_unique_page_by_idx(self.target, tar_idx, self.Ttars_idx,
                                           'title'):
            print(self.target_by_idx)
            return tar
        return None

    def create_tar_by_date(self, date_val: Union[dt.datetime, dt.date]):
        tar = self.target.rows.open_new_page()
        date_handler = DateHandler(date_val)

        tar_idx = date_handler.strf_dig6_and_weekday()
        tar.props.write(tag=self.Ttars_idx, value=tar_idx)

        date_range = DateObject(date_handler.date)
        writer = tar.props
        writer.write_date(tag=self.Ttars_date, value=date_range)
        return tar.save()


class DateMatcherofDoublyLinked(DateMatcherAbs):
    Tdoms_tar1 = 'to_created_dates'
    Tdoms_tar2 = 'to_dates'

    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.journals, self.bs.schedules]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if tar := self.match_dates(dom):
                    dom.props.write_relation(tag=self.Tdoms_tar2,
                                             value=tar.block_id)
                    PeriodResetter.process(dom)
                if tar := self.match_created_dates(dom):
                    dom.props.write_relation(tag=self.Tdoms_tar1, value=tar.block_id)

    def match_dates(self, dom: PageRow):
        if dom.props.read_tag(self.Tdoms_tar2):
            return None
        return self.determine_tar_from_auto_date(dom)

    def match_created_dates(self, dom: PageRow):
        if dom.props.read_tag(self.Tdoms_tar1):
            return None
        return self.determine_tar_from_auto_date(dom)


class DateMatcherviaReference(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.tasks]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if tar := self.determine_tar(dom):
                    dom.props.write_relation(tag=self.T_tar, value=tar.block_id)

    def determine_tar(self, dom: PageRow):
        if dom.props.read_tag(self.T_tar):
            return None
        if ref := fetch_unique_page_of_relation(dom, self.reference, self.Tdoms_ref):
            if tar := fetch_unique_page_of_relation(ref, self.target, self.T_tar):
                return tar
            return None
        return self.determine_tar_from_auto_date(dom)


class DateMatcherofWritings(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.writings

    def execute(self):
        for dom in self.domain.rows:
            if tar := self.match_dates(dom):
                dom.props.write_relation(tag=self.T_tar, value=tar.block_id)

    def match_dates(self, dom: PageRow):
        if dom.props.read_tag(self.T_tar):
            return None
        return self.determine_tar_from_auto_date(dom)


class DateMatcherofMultipleCardinality(DateMatcherAbs, metaclass=ABCMeta):
    def determine_earliest_tar(self, dom: PageRow,
                               reference: Database, doms_ref, refs_tar):
        refs = fetch_all_pages_of_relation(dom, reference, doms_ref)
        tars = []
        for ref in refs:
            new_tars = fetch_all_pages_of_relation(ref, self.target, refs_tar)
            tars.extend(new_tars)
        earliest_tar: Optional[PageRow] = None
        earliest_date = None
        for tar in tars:
            date = tar.props.read_tag(self.Ttars_date)
            if earliest_date is None or date < earliest_date:
                earliest_tar = tar
                earliest_date = date
        return earliest_tar


class DateMatcherofReadings(DateMatcherofMultipleCardinality):
    Tdoms_ref2 = 'to_schedules'
    Tref2s_tar = 'to_dates'

    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.readings
        self.reference2 = self.bs.schedules

    def execute(self):
        for dom in self.domain.rows:
            if tar := self.match_dates(dom):
                dom.props.write_relation(tag=self.T_tar, value=tar.block_id)
                PeriodResetter.process(dom)

    def match_dates(self, dom: PageRow):
        if dom.props.read_tag(self.T_tar):
            return None
        if dom.props.read_tag('no_exp'):
            return None
        if tar := self.determine_earliest_tar(dom, self.reference, self.Tdoms_ref,
                                              self.T_tar):
            return tar
        if tar := self.determine_earliest_tar(dom, self.reference2, self.Tdoms_ref2,
                                              self.Tref2s_tar):
            return tar
        if dom.props.read_tag('is_book'):
            return None
        if tar := self.determine_tar_from_auto_date(dom):
            return tar
        return None


class DateMatcherofJournalsDepr(DateMatcherAbs):
    Tdoms_updom = 'up_self'

    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.journals]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if tar := self.determine_tar(dom):
                    writer = dom.props
                    writer.write_relation(tag=self.T_tar, value=tar.block_id)

    def determine_tar(self, dom: PageRow):
        if dom.props.read_tag(self.T_tar):
            return None
        # if ref := fetch_unique_page_of_relation(dom, dom.parent, self.Tdoms_updom):
        #     if tar := fetch_unique_page_of_relation(ref, self.target, self.T_tar):
        #         return tar
        #     return None
        return self.determine_tar_from_auto_date(dom)


class DateDomainFillerDepr(DateMatcherAbs):
    Tdoms_date = 'manual_date'
    Ttimestr = 'timestr'

    def __init__(self, bs, disable_overwrite=False):
        super().__init__(bs)
        self.disable_overwrite = disable_overwrite
        self.domains_type1 = [
            self.bs.journals, self.bs.writings,
        ]
        self.domains_type2 = [
            self.bs.tasks, self.bs.schedules,
        ]

    def execute(self):
        self.bs.root.disable_overwrite = self.disable_overwrite
        for domain in self.domains_type1:
            for dom in domain.rows:
                self.update_type1(dom)
        for domain in self.domains_type2:
            for dom in domain.rows:
                self.update_type2(dom)
        self.bs.root.disable_overwrite = False

    def update_type1(self, dom: PageRow):
        if date_val := self.get_date_val(dom):
            if time_val := self.get_time_val(dom):
                dt_val = dt.datetime.combine(date_val, time_val[0])
            else:
                dt_val = date_val
            if dt_val != dom.props.read_tag(self.Tdoms_date):
                dom.props.write_date(tag=self.Tdoms_date, value=dt_val)

    def update_type2(self, dom: PageRow):
        if date_val := self.get_date_val(dom):
            if date_val != dom.props.read_tag(self.Tdoms_date):
                dom.props.write_date(tag=self.Tdoms_date, value=date_val)

    def get_date_val(self, dom: PageRow):
        tar_ids = dom.props.read_tag(self.T_tar)
        tar = self.target.rows.fetch(tar_ids[0])
        date_val: DateObject = tar.props.read_tag(self.Ttars_date)
        return date_val.start_date

    def get_time_val(self, dom: PageRow):
        if timestr := dom.props.read_tag(self.Ttimestr):
            return TimeStringHandler(timestr).time_val
        return None
import datetime as dt
from abc import ABCMeta
from typing import Optional, Union

from notion_zap.cli import editors
from notion_zap.cli.struct import DateFormat
from ..common.date_handler import DateHandler
from ..common.dt_handler import TimeStringHandler
from ..common.helpers import (
    query_unique_page_by_idx,
    fetch_all_pages_of_relation, fetch_unique_page_of_relation
)
from ..common.struct import RoutineManager


class DateMatcherAbs(RoutineManager, metaclass=ABCMeta):
    Tdoms_ref = 'to_journals'
    Tdoms_date = 'auto_datetime'
    T_tar = 'to_dates'
    Ttars_idx = 'title'
    Ttars_date = 'manual_date'
    target_by_idx: dict[str, editors.PageRow] = {}
    # this boolean flag is SHARED by all implemented classes,
    #  so that prevent it from being initialized multiple times.
    target_by_idx_initalized = False

    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.dates
        self.reference = self.bs.journals

    @classmethod
    def initalize_idx(cls, self):
        if not cls.target_by_idx_initalized:
            cls.target_by_idx = self.target.pages.by_idx_at(cls.Ttars_idx)
            cls.target_by_idx_initalized = True

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
            self.target_by_idx.update({tar_idx: tar})
            return tar
        return None

    def create_tar_by_date(self, date_val: Union[dt.datetime, dt.date]):
        tar = self.target.pages.create_page()
        date_handler = DateHandler(date_val)

        tar_idx = date_handler.strf_dig6_and_weekday()
        tar.props.write_at(self.Ttars_idx, tar_idx)
        self.target_by_idx.update({tar_idx: tar})

        date_range = DateFormat(date_handler.date)
        tar.props.write_date_at(self.Ttars_date, date_range)
        return tar.save()


class DateMatcherType1(DateMatcherAbs):
    Tdoms_updom = 'up_self'

    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.journals]

    def execute(self):
        self.initalize_idx(self)
        for domain in self.domains:
            for dom in domain.pages:
                if tar := self.determine_tar(dom, domain):
                    dom.props.write_relation_at(self.T_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow, domain: editors.Database):
        if dom.props.read_at(self.T_tar):
            return None
        if ref := fetch_unique_page_of_relation(dom, domain, self.Tdoms_updom):
            if tar := fetch_unique_page_of_relation(ref, self.target, self.T_tar):
                return tar
            return None
        return self.determine_tar_from_auto_date(dom)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at(self.Tdoms_date)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_tar_by_date(date_val)


class DateMatcherType2(DateMatcherAbs):
    Tdoms_tar1 = 'to_created_dates'
    Tdoms_tar2 = 'to_scheduled_dates'

    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.schedules]

    def execute(self):
        self.initalize_idx(self)
        for domain in self.domains:
            for dom in domain.pages:
                if tar := self.match_created_dates(dom):
                    dom.props.write_relation_at(self.Tdoms_tar1, tar.block_id)
                if tar := self.match_scheduled_dates(dom):
                    dom.props.write_relation_at(self.Tdoms_tar2, tar.block_id)

    def match_created_dates(self, dom: editors.PageRow):
        if dom.props.read_at(self.Tdoms_tar1):
            return None
        return self.determine_tar_from_auto_date(dom)

    def match_scheduled_dates(self, dom):
        if dom.props.read_at(self.Tdoms_tar2):
            return None
        return self.determine_tar_from_auto_date(dom)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at(self.Tdoms_date)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_tar_by_date(date_val)


class DateMatcherType3(DateMatcherAbs):
    Tdoms_ref2 = 'to_schedules'
    Tref2s_tar = 'to_scheduled_dates'

    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.writings, self.bs.readings]
        self.reference2 = self.bs.schedules

    def execute(self):
        self.initalize_idx(self)
        for domain in self.domains:
            for dom in domain.pages:
                if tar := self.match_dates(dom):
                    dom.props.write_relation_at(self.T_tar, tar.block_id)

    def match_dates(self, dom: editors.PageRow):
        if dom.props.read_at(self.T_tar):
            return None
        if dom.parent is self.bs.readings and dom.props.read_at('status_exclude'):
            return None
        if tar := self.determine_tar_from_ref(
                dom, self.reference, self.Tdoms_ref, self.T_tar):
            return tar
        if tar := self.determine_tar_from_ref(
                dom, self.reference2, self.Tdoms_ref2, self.Tref2s_tar):
            return tar
        if dom.parent is self.bs.readings and dom.props.read_at('is_book'):
            return None
        if tar := self.determine_tar_from_auto_date(dom):
            return tar
        return None

    def determine_tar_from_ref(self, dom: editors.PageRow,
                               reference: editors.Database, doms_ref, refs_tar):
        refs = fetch_all_pages_of_relation(dom, reference, doms_ref)
        tars = []
        for ref in refs:
            new_tars = fetch_all_pages_of_relation(ref, self.target, refs_tar)
            tars.extend(new_tars)
        earliest_tar: Optional[editors.PageRow] = None
        earliest_date = None
        for tar in tars:
            date = tar.props.read_at(self.Ttars_date)
            if earliest_date is None or date < earliest_date:
                earliest_tar = tar
                earliest_date = date
        return earliest_tar

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx = dom.props.read_at(self.Tdoms_date)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_tar_by_date(date_val)


class DateMatcherType4(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.memos]

    def execute(self):
        self.initalize_idx(self)
        for domain in self.domains:
            for dom in domain.pages:
                if tar := self.determine_tar(dom):
                    dom.props.write_relation_at(self.T_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow):
        if dom.props.read_at(self.T_tar):
            return None
        if ref := fetch_unique_page_of_relation(dom, self.reference, self.Tdoms_ref):
            if tar := fetch_unique_page_of_relation(ref, self.target, self.T_tar):
                return tar
            return None
        return self.determine_tar_from_auto_date(dom)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at(self.Tdoms_date)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_tar_by_date(date_val)


class DateTargetFiller(DateMatcherAbs):
    def __init__(self, bs, disable_overwrite: bool, create_date_range=None):
        super().__init__(bs)
        from ..build_calendar import CalendarDateRange
        self.create_date_range: CalendarDateRange = create_date_range
        self.disable_overwrite = disable_overwrite

    def execute(self):
        self.bs.root.disable_overwrite = self.disable_overwrite
        for tar in self.target.pages:
            self.update_tar(tar)
        if self.create_date_range:
            for date_val in self.create_date_range.iter_date():
                if self.find_tar_by_date(date_val):
                    continue
                self.create_tar_by_date(date_val)
        self.bs.root.disable_overwrite = False

    def update_tar(self, tar: editors.PageRow, tar_idx=None):
        """provide tar_idx manually if yet not synced to server-side"""
        if tar_idx is None:
            tar_idx = tar.props.read_at(self.Ttars_idx)
        date_handler = DateHandler.from_strf_dig6(tar_idx)
        new_tar_idx = date_handler.strf_dig6_and_weekday()
        if tar_idx != new_tar_idx:
            tar.props.write_date_at(self.Ttars_idx, new_tar_idx)
        date_range = DateFormat(date_handler.date)
        if date_range != tar.props.read_at(self.Ttars_date):
            tar.props.write_date_at(self.Ttars_date, date_range)
            tar.save_preview()
            tar.save()
        # print(f"{tar=}, {tar_idx=}, {date_range=},"
        #       f"{tar.props.read_at(self.Ttars_date)=},"
        #       f"{date_range != tar.props.read_at(self.Ttars_date)=}")


# deprecated

class DateDomainFiller(DateMatcherAbs):
    Tdoms_date = 'manual_date'
    Ttimestr = 'timestr'

    def __init__(self, bs, disable_overwrite=False):
        super().__init__(bs)
        self.disable_overwrite = disable_overwrite
        self.domains_type1 = [
            self.bs.journals, self.bs.writings,
        ]
        self.domains_type2 = [
            self.bs.memos, self.bs.schedules,
        ]

    def execute(self):
        self.initalize_idx(self)
        self.bs.root.disable_overwrite = self.disable_overwrite
        for domain in self.domains_type1:
            for dom in domain.pages:
                self.update_type1(dom)
        for domain in self.domains_type2:
            for dom in domain.pages:
                self.update_type2(dom)
        self.bs.root.disable_overwrite = False

    def update_type1(self, dom: editors.PageRow):
        if date_val := self.get_date_val(dom):
            if time_val := self.get_time_val(dom):
                dt_val = dt.datetime.combine(date_val, time_val[0])
            else:
                dt_val = date_val
            if dt_val != dom.props.read_at(self.Tdoms_date):
                dom.props.write_date_at(self.Tdoms_date, dt_val)

    def update_type2(self, dom: editors.PageRow):
        if date_val := self.get_date_val(dom):
            if date_val != dom.props.read_at(self.Tdoms_date):
                dom.props.write_date_at(self.Tdoms_date, date_val)

    def get_date_val(self, dom: editors.PageRow):
        tar_ids = dom.props.read_at(self.T_tar)
        tar = self.target.pages.fetch(tar_ids[0])
        date_val: DateFormat = tar.props.read_at(self.Ttars_date)
        return date_val.start_date

    def get_time_val(self, dom: editors.PageRow):
        if timestr := dom.props.read_at(self.Ttimestr):
            return TimeStringHandler(timestr).time_val
        return None

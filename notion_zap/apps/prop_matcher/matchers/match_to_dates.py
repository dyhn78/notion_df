from abc import ABCMeta
from typing import Optional
import datetime as dt

from notion_zap.cli import editors
from notion_zap.cli.struct import DateFormat
from ..common.struct import Matcher
from ..common.date_handler import DateHandler
from ..common.helpers import (
    overwrite_prop,
    query_target_by_idx,
    fetch_all_pages_from_relation, fetch_unique_page_from_relation
)


class DateMatcherAbs(Matcher, metaclass=ABCMeta):
    doms_ref = 'to_journals'
    doms_date_val = 'auto_datetime'
    doms_tar = refs_tar = 'to_dates'
    tars_idx = 'title'
    tars_date_val = 'manual_date'

    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.dates
        self.reference = self.bs.journals
        self.tars_by_index = self.bs.dates.by_idx_value_at(self.tars_idx)

    def find_or_create_by_date_val(self, date_val: dt.datetime):
        if tar := self.find_by_date_val(date_val):
            return tar
        return self.create_by_date_val(date_val)

    def find_by_date_val(self, date_val: dt.datetime):
        date_handler = DateHandler(date_val)
        tar_idx_val = date_handler.strf_dig6_and_weekday()
        if tar := self.tars_by_index.get(tar_idx_val):
            return tar
        if tar := query_target_by_idx(self.target, tar_idx_val, self.tars_idx, 'title'):
            self.tars_by_index.update({tar_idx_val: tar})
            return tar
        return None

    def create_by_date_val(self, date_val: dt.datetime):
        tar = self.target.create_page()
        date_handler = DateHandler(date_val)

        tar_idx_val = date_handler.strf_dig6_and_weekday()
        tar.props.write_at(self.tars_idx, tar_idx_val)
        self.tars_by_index.update({tar_idx_val: tar})

        date_range = DateFormat(date_handler.date)
        tar.props.write_date_at(self.tars_date_val, date_range)
        return tar.save()

    def update_tar(self, tar: editors.PageRow, tar_idx_val=None,
                   disable_overwrite=False):
        """provide tar_idx_val manually if yet not synced to server-side"""
        if tar_idx_val is None:
            tar_idx_val = tar.props.read_at(self.tars_idx)
        date_handler = DateHandler.from_strf_dig6(tar_idx_val)
        date_range = DateFormat(date_handler.date)
        if date_range != tar.props.read_at(self.tars_date_val):
            self.bs.root.disable_overwrite = disable_overwrite
            tar.props.write_date_at(self.tars_date_val, date_range)
            self.bs.root.disable_overwrite = False


class DateTargetAutoFiller(DateMatcherAbs):
    def __init__(self, bs, disable_overwrite, create_date_range):
        super().__init__(bs)
        from ..calendar import CalendarDateRange
        self.create_date_range: CalendarDateRange = create_date_range
        self.disable_overwrite = disable_overwrite

    def execute(self):
        for tar in self.target:
            self.update_tar(tar, disable_overwrite=self.disable_overwrite)
        if self.create_date_range:
            for date_val in self.create_date_range.iter_date():
                if self.find_by_date_val(date_val):
                    continue
                self.create_by_date_val(date_val)


class DateMatcherType1(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.journals]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if bool(dom.props.read_at(self.refs_tar)):
                    continue
                if tar := self.determine_tar(dom, domain):
                    overwrite_prop(dom, self.doms_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow, domain: editors.PageList):
        if ref := fetch_unique_page_from_relation(dom, domain, 'up_self'):
            if tar := fetch_unique_page_from_relation(ref, self.target, self.refs_tar):
                return tar
            return None
        return self.determine_tar_from_auto_date(dom)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at(self.doms_date_val)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_by_date_val(date_val)


class DateMatcherType2(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.writings, self.bs.memos]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if bool(dom.props.read_at(self.refs_tar)):
                    continue
                if tar := self.determine_tar(dom):
                    overwrite_prop(dom, self.refs_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow):
        if ref := fetch_unique_page_from_relation(dom, self.reference, self.doms_ref):
            if tar := fetch_unique_page_from_relation(
                    ref, self.target, self.refs_tar):
                return tar
            return None
        return self.determine_tar_from_auto_date(dom)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at(self.doms_date_val)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_by_date_val(date_val)


class DateMatcherType3(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.schedules]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if bool(dom.props.read_at(self.refs_tar)):
                    continue
                if tar := self.determine_tar_from_auto_date(dom):
                    overwrite_prop(dom, self.doms_tar, tar.block_id)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at(self.doms_date_val)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_by_date_val(date_val)


class DateMatcherType4(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.readings]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if self.exclude_match(dom):
                    continue
                if tar := self.determine_tar(dom):
                    overwrite_prop(dom, self.doms_tar, tar.block_id)

    def exclude_match(self, dom: editors.PageRow):
        return (dom.props.read_at(self.refs_tar)
                or dom.props.read_at('status_exclude'))

    def determine_tar(self, dom: editors.PageRow):
        if tar := self.determine_tar_from_ref(dom):
            return tar
        if tar := self.determine_tar_from_auto_date(dom):
            return tar
        return None

    def determine_tar_from_ref(self, dom: editors.PageRow):
        refs = fetch_all_pages_from_relation(dom, self.reference, self.doms_ref)
        tars = []
        for ref in refs:
            new_tars = fetch_all_pages_from_relation(ref, self.target, self.refs_tar)
            tars.extend(new_tars)
        earliest_tar: Optional[editors.PageRow] = None
        earliest_date = None
        for tar in tars:
            date = tar.props.read_at(self.tars_date_val)
            if earliest_date is None or date < earliest_date:
                earliest_tar = tar
                earliest_date = date
        return earliest_tar

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx = dom.props.read_at(self.doms_date_val)
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        return self.find_or_create_by_date_val(date_val)

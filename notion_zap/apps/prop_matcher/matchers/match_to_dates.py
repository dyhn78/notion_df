from abc import ABCMeta
from typing import Optional
import datetime as dt

from notion_zap.cli import editors
from notion_zap.cli.struct import DateFormat
from ..common.base import Matcher
from ..common.date_handler import DateHandler
from ..common.helpers import (
    overwrite_prop,
    query_target_by_idx,
    fetch_all_pages_from_relation, fetch_unique_page_from_relation
)


class DateMatcherAbs(Matcher, metaclass=ABCMeta):
    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.dates
        self.to_tar = 'to_dates'
        self.to_ref = 'to_journals'
        self.tars_by_index = self.bs.dates.by_idx_value_at('index_as_target')

    def find_or_create_by_date_val(self, date_val: dt.datetime):
        if tar := self.find_by_date_val(date_val):
            return tar
        return self.create_by_date_val(date_val)

    def find_by_date_val(self, date_val: dt.datetime):
        date_handler = DateHandler(date_val)
        tar_idx = date_handler.strf_dig6_and_weekday()
        if tar := self.tars_by_index.get(tar_idx):
            return tar
        if tar := query_target_by_idx(self.target, tar_idx, 'title'):
            self.tars_by_index.update({tar_idx: tar})
            return tar
        return None

    def create_by_date_val(self, date_val: dt.datetime):
        tar = self.target.create_page()
        date_handler = DateHandler(date_val)

        tar_idx = date_handler.strf_dig6_and_weekday()
        tar.props.write_at('index_as_target', tar_idx)
        self.tars_by_index.update({tar_idx: tar})

        date_range = DateFormat(date_handler.date)
        tar.props.write_date_at('manual_date', date_range)
        return tar.save()

    def update_tar(self, tar: editors.PageRow, tar_idx=None,
                   disable_overwrite=False):
        """provide tar_idx manually if yet not synced to server-side"""
        if tar_idx is None:
            tar_idx = tar.props.read_at('index_as_target')
        date_handler = DateHandler.from_strf_dig6(tar_idx)
        date_range = DateFormat(date_handler.date)
        if date_range != tar.props.read_at('manual_date'):
            self.bs.root.disable_overwrite = disable_overwrite
            tar.props.write_date_at('manual_date', date_range)
            self.bs.root.disable_overwrite = False


class DateTargetAutoFiller(DateMatcherAbs):
    def __init__(self, bs, disable_overwrite, create_date_range):
        super().__init__(bs)
        self.disable_overwrite = disable_overwrite
        from ..calendar import DateRange
        self.create_date_range: DateRange = create_date_range

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
                if bool(dom.props.read_at(self.to_tar)):
                    continue
                tar = self.determine_tar(dom, domain)
                overwrite_prop(dom, self.to_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow, domain: editors.PageList):
        if ref := fetch_unique_page_from_relation(dom, domain, 'up_self'):
            if tar := fetch_unique_page_from_relation(ref, self.target, self.to_tar):
                return tar
            return None
        return self.determine_tar_from_auto_date(dom)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at('index_as_domain')
        date_val = dom_idx.start - dt.timedelta(-5)
        return self.find_or_create_by_date_val(date_val)


class DateMatcherType2(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.journals
        self.domains = [self.bs.writings, self.bs.memos, self.bs.schedules]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if bool(dom.props.read_at(self.to_tar)):
                    continue
                if tar := self.determine_tar(dom):
                    overwrite_prop(dom, self.to_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow):
        if ref := fetch_unique_page_from_relation(dom, self.reference, self.to_ref):
            if tar := fetch_unique_page_from_relation(ref, self.target, self.to_tar):
                return tar
            return ''
        return self.determine_tar_from_auto_date(dom)

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at('index_as_domain')
        date_val = dom_idx.start - dt.timedelta(-5)
        return self.find_or_create_by_date_val(date_val)


class DateMatcherType3(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.journals
        self.domains = [self.bs.readings]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if bool(dom.props.read_at(self.to_tar)):
                    continue
                if tar := self.determine_tar(dom):
                    overwrite_prop(dom, self.to_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow):
        if dom.props.read_at('status_exclude'):
            return None
        if tar := self.determine_tar_from_ref(dom):
            return tar
        if tar := self.determine_tar_from_auto_date(dom):
            return tar
        return None

    def determine_tar_from_ref(self, dom: editors.PageRow):
        refs = fetch_all_pages_from_relation(dom, self.reference, self.to_ref)
        tars = []
        for ref in refs:
            new_tars = fetch_all_pages_from_relation(ref, self.target, self.to_tar)
            for tar in new_tars:
                if tar not in tars:
                    tars.append(tar)
        earliest_tar: Optional[editors.PageRow] = None
        earliest_date = None
        for tar in tars:
            date = tar.props.read_at('manual_date')
            if earliest_date is None or date < earliest_date:
                earliest_tar = tar
                earliest_date = date
        return earliest_tar

    def determine_tar_from_auto_date(self, dom: editors.PageRow):
        dom_idx = dom.props.read_at('index_as_domain')
        date_val = dom_idx.start - dt.timedelta(-5)
        return self.find_or_create_by_date_val(date_val)


class DateMatcherType4(DateMatcherAbs):
    def execute(self):
        pass
        # algorithm = TernaryMatchAlgorithm(self.journals, None, self.dates)
        # algorithm.by_ref('to_themes', 'to_dates', 'to_themes')

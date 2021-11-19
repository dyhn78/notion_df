from abc import ABCMeta
import datetime as dt

from notion_zap.cli import editors
from notion_zap.cli.struct import DateFormat
from ..common.struct import Matcher
from ..common.date_handler import DateHandler
from ..common.helpers import (
    overwrite_prop,
    fetch_unique_page_from_relation,
    query_target_by_idx
)


class PeriodMatcherAbs(Matcher, metaclass=ABCMeta):
    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.periods
        self.to_tar = 'to_periods'
        self.tars_by_index = self.target.by_idx_value_at('index_as_target')

    def find_by_date_val(self, date_val: dt.date):
        date_handler = DateHandler(date_val)
        tar_idx = date_handler.strf_year_and_week()
        if tar := self.tars_by_index.get(tar_idx):
            return tar
        if tar := query_target_by_idx(self.target, tar_idx, 'text'):
            self.tars_by_index.update({tar_idx: tar})
            return tar
        return None

    def create_by_date_val(self, date_val: dt.date):
        tar = self.target.create_page()
        date_handler = DateHandler(date_val)

        tar_idx = date_handler.strf_year_and_week()
        tar.props.write_title_at('index_as_target', tar_idx)
        self.tars_by_index.update({tar_idx: tar})

        date_range = DateFormat(start=date_handler.first_day_of_week(),
                                end=date_handler.last_day_of_week())
        tar.props.write_date_at('manual_date_range', date_range)
        return tar.save()

    def update_tar(self, tar: editors.PageRow, tar_idx=None,
                   disable_overwrite=False):
        """provide tar_idx manually if yet not synced to server-side"""
        if tar_idx is None:
            tar_idx = tar.props.read_at('index_as_target')
        date_handler = DateHandler.from_strf_year_and_week(tar_idx)

        date_range = DateFormat(start=date_handler.first_day_of_week(),
                                end=date_handler.last_day_of_week())
        if date_range != tar.props.read_at('manual_date_range'):
            self.bs.root.disable_overwrite = disable_overwrite
            tar.props.write_date_at('manual_date_range', date_range)
            self.bs.root.disable_overwrite = False


class PeriodTargetAutoFiller(PeriodMatcherAbs):
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


class PeriodMatcherType1(PeriodMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.dates]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if dom.props.read_at(self.to_tar):
                    continue
                tar = self.determine_tar(dom)
                overwrite_prop(dom, self.to_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow):
        dom_idx: DateFormat = dom.props.read_at('index_as_domain')
        date_val = dom_idx.start
        if tar := self.find_by_date_val(date_val):
            return tar
        return self.create_by_date_val(date_val)


class PeriodMatcherType2(PeriodMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.dates
        self.to_ref = 'to_dates'
        self.domains = [
            self.bs.journals, self.bs.writings, self.bs.memos, self.bs.schedules,
            self.bs.readings
        ]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if dom.props.read_at(self.to_tar):
                    continue
                if tar := self.determine_tar(dom):
                    overwrite_prop(dom, self.to_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow):
        if ref := fetch_unique_page_from_relation(dom, self.reference, self.to_ref):
            if tar := fetch_unique_page_from_relation(ref, self.target, self.to_tar):
                return tar
        return None


class PeriodMatcherType3(PeriodMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.dates
        self.to_tar = 'to_scheduled_periods'
        self.to_ref = 'to_scheduled_dates'
        self.from_ref_to_tar = 'to_periods'
        self.domains = [self.bs.schedules]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if dom.props.read_at(self.to_tar):
                    continue
                if tar := self.determine_tar(dom):
                    overwrite_prop(dom, self.to_tar, tar.block_id)

    def determine_tar(self, dom: editors.PageRow):
        dom.reads()
        if ref := fetch_unique_page_from_relation(dom, self.reference, self.to_ref):
            ref.reads()
            if tar := fetch_unique_page_from_relation(
                    ref, self.target, self.from_ref_to_tar):
                return tar
        return None

from abc import ABCMeta
import datetime as dt

from notion_zap.cli import editors
from notion_zap.cli.structs import DateObject
from ..common.struct import EditorManager
from ..common.date_handler import DateHandler
from ..common.helpers import (
    fetch_unique_page_of_relation,
    query_unique_page_by_idx
)


class PeriodMatcherAbs(EditorManager, metaclass=ABCMeta):
    T_tar = 'to_periods'
    Ttars_idx = 'title'
    Ttars_date = 'manual_date_range'

    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.periods
        self.target_by_idx = self.target.rows.index_by_tag(self.Ttars_idx)

    def find_or_create_by_date_val(self, date_val: dt.date):
        if tar := self.find_by_date_val(date_val):
            return tar
        return self.create_by_date_val(date_val)

    def find_by_date_val(self, date_val: dt.date):
        if not date_val:
            return None
        date_handler = DateHandler(date_val)
        tar_idx = date_handler.strf_year_and_week()
        if tar := self.target_by_idx.get(tar_idx):
            return tar
        if tar := query_unique_page_by_idx(self.target, tar_idx, self.Ttars_idx,
                                           'title'):
            self.target_by_idx.update({tar_idx: tar})
            return tar
        return None

    def create_by_date_val(self, date_val: dt.date):
        if not date_val:
            return None
        tar = self.target.rows.open_new_page()
        date_handler = DateHandler(date_val)

        tar_idx = date_handler.strf_year_and_week()
        writer = tar.props
        writer.write_title(tag=self.Ttars_idx, value=tar_idx)
        self.target_by_idx.update({tar_idx: tar})

        date_range = DateObject(start=date_handler.first_day_of_week(),
                                end=date_handler.last_day_of_week())
        property_writer = tar.props
        property_writer.write_date(tag=self.Ttars_date, value=date_range)
        return tar.save()

    def update_tar(self, tar: editors.PageRow, tar_idx=None,
                   disable_overwrite=False):
        """provide tar_idx manually if yet-not-synced to server-side"""
        if tar_idx is None:
            tar_idx = tar.props.read_tag(self.Ttars_idx)
        date_handler = DateHandler.from_strf_year_and_week(tar_idx)

        date_range = DateObject(start=date_handler.first_day_of_week(),
                                end=date_handler.last_day_of_week())
        if date_range != tar.props.read_tag(self.Ttars_date):
            self.bs.root.disable_overwrite = disable_overwrite
            writer = tar.props
            writer.write_date(tag=self.Ttars_date, value=date_range)
            self.bs.root.disable_overwrite = False


class PeriodMatcherType1(PeriodMatcherAbs):
    Tdoms_date = 'manual_date'

    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.dates]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if tar := self.match_periods(dom):
                    writer = dom.props
                    writer.write_relation(tag=self.T_tar, value=tar.block_id)

    def match_periods(self, dom: editors.PageRow):
        if dom.props.read_tag(self.T_tar):
            return None
        dom_idx: DateObject = dom.props.read_tag(self.Tdoms_date)
        date_val = dom_idx.start_date
        return self.find_or_create_by_date_val(date_val)


class PeriodMatcherType2(PeriodMatcherAbs):
    Tdoms_ref = 'to_dates'

    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.dates
        self.domains = [
            self.bs.journals, self.bs.writings, self.bs.memos,
            self.bs.readings
        ]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if tar := self.match_periods(dom):
                    writer = dom.props
                    writer.write_relation(tag=self.T_tar, value=tar.block_id)

    def match_periods(self, dom: editors.PageRow):
        if dom.props.read_tag(self.T_tar):
            return None
        if ref := fetch_unique_page_of_relation(dom, self.reference, self.Tdoms_ref):
            if tar := fetch_unique_page_of_relation(ref, self.target, self.T_tar):
                return tar
        return None


class PeriodMatcherType3(PeriodMatcherAbs):
    Tdoms_ref1 = 'to_created_dates'
    Tdoms_tar1 = 'to_created_periods'
    Tdoms_ref2 = 'to_scheduled_dates'
    Tdoms_tar2 = 'to_scheduled_periods'

    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.dates
        self.domains = [self.bs.schedules]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if tar := self.match_created_periods(dom):
                    dom.props.write_relation(tag=self.Tdoms_tar1, value=tar.block_id)
                if tar := self.match_scheduled_periods(dom):
                    dom.props.write_relation(tag=self.Tdoms_tar2, value=tar.block_id)

    def match_created_periods(self, dom: editors.PageRow):
        if dom.props.read_tag(self.Tdoms_tar1):
            return None
        if ref := fetch_unique_page_of_relation(dom, self.reference, self.Tdoms_ref1):
            if tar := fetch_unique_page_of_relation(ref, self.target, self.T_tar):
                return tar
        return None

    def match_scheduled_periods(self, dom: editors.PageRow):
        if dom.props.read_tag(self.Tdoms_tar2):
            return None
        if ref := fetch_unique_page_of_relation(dom, self.reference, self.Tdoms_ref2):
            if tar := fetch_unique_page_of_relation(ref, self.target, self.T_tar):
                return tar
        return None


class PeriodTargetFiller(PeriodMatcherAbs):
    def __init__(self, bs, disable_overwrite, create_date_range):
        super().__init__(bs)
        self.disable_overwrite = disable_overwrite
        from ..build_calendar import CalendarDateRange
        self.create_date_range: CalendarDateRange = create_date_range

    def execute(self):
        for tar in self.target:
            self.update_tar(tar, disable_overwrite=self.disable_overwrite)
        if self.create_date_range:
            for date_val in self.create_date_range.iter_date():
                if self.find_by_date_val(date_val):
                    continue
                self.create_by_date_val(date_val)

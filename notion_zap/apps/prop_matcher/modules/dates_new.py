from __future__ import annotations

import datetime as dt
from typing import Optional, Union, Hashable

from notion_zap.cli.editors import PageRow, Database
from notion_zap.cli.structs import DateObject
from ..common.date_handler import DateHandler
from ..common.helpers import (
    query_unique_page_by_idx,
    fetch_unique_page_of_relation,
    fetch_all_pages_of_relation
)
from ..common.struct import RowFunction, EditorBase, RootFunction


class DatesModule(RootFunction):
    def __init__(self, bs: EditorBase):
        super().__init__(bs)
        self.no_replace = True

    def __call__(self):
        get_by_created_date = GetterByCreatedDate(self.bs.dates)
        for table, tag_date in self.targets_using_created_date:
            for row in table.rows:
                if self.skip(row, tag_date):
                    continue
                if date := get_by_created_date(row):
                    self.set_date(row, date, tag_date)

        for table, tag_date, ref_args in self.targets_using_earliest_ref:
            get_by_earliest_ref = GetterByEarliestRef(self.bs.dates, ref_args)
            for row in table.rows:
                if self.skip(row, tag_date):
                    continue
                if date := get_by_earliest_ref(row):
                    self.set_date(row, date, tag_date)

    def skip(self, row: PageRow, tag_date):
        return self.no_replace and bool(row.read_tag(tag_date))

    @staticmethod
    def set_date(row: PageRow, date: PageRow, tag_date):
        row.write_relation(tag=tag_date, value=date.block_id)

    @property
    def targets_using_created_date(self):
        targets = []
        for table in [
            self.bs.journals,
            self.bs.checks,
            self.bs.topics,
            self.bs.writings,
            self.bs.tasks,
        ]:
            targets.append((table, 'dates'))
        for table in [
            self.bs.journals,
            self.bs.checks,
            self.bs.readings,
        ]:
            targets.append((table, 'dates_created'))
        return targets

    @property
    def targets_using_earliest_ref(self):
        return [
            (self.bs.readings, 'dates_begin',
             [ReferenceArgument(self.bs.checks, 'checks', 'dates')])
        ]


class GetterByCreatedDate(RowFunction):
    def __init__(self, dates: Database):
        self.dates = dates
        self.target_by_idx = self.dates.rows.index_by_tag('title')

    def __call__(self, row: PageRow):
        dom_idx: DateObject = row.read_tag('auto_datetime')
        date_val = dom_idx.start + dt.timedelta(hours=-5)
        if tar := self.find_tar_by_date(date_val):
            return tar
        return self.create_tar_by_date(date_val)

    def find_tar_by_date(self, date_val: Union[dt.datetime, dt.date]):
        date_handler = DateHandler(date_val)
        tar_idx = date_handler.strf_dig6_and_weekday()
        if tar := self.target_by_idx.get(tar_idx):
            return tar
        if tar := query_unique_page_by_idx(self.dates, tar_idx, 'title',
                                           'title'):
            return tar
        return None

    def create_tar_by_date(self, date_val: Union[dt.datetime, dt.date]):
        tar = self.dates.rows.open_new_page()
        date_handler = DateHandler(date_val)

        tar_idx = date_handler.strf_dig6_and_weekday()
        tar.write(tag='title', value=tar_idx)

        date_range = DateObject(date_handler.date)
        tar.write_date(tag='dateval_manual', value=date_range)
        return tar.save()


class ReferenceArgument:
    def __init__(
            self, reference: Database, tag_ref: Hashable, refs_tag_date: Hashable):
        self.reference = reference
        self.tag_ref = tag_ref
        self.refs_tag_date = refs_tag_date


class GetterByEarliestRef:
    def __init__(self, dates: Database, args: list[ReferenceArgument]):
        self.dates = dates
        self.args = args

    def __call__(self, row: PageRow):
        collector = EarliestDateFinder(row, self.dates)
        for arg in self.args:
            collector.collect_dates_via_reference(
                arg.reference, arg.tag_ref, arg.refs_tag_date)
        return collector.earliest_date_row


class EarliestDateFinder:
    def __init__(self, row: PageRow, dates: Database):
        self.row = row
        self.dates = dates
        self.earliest_date_row: Optional[PageRow] = None
        self.earliest_date_val = None

    def collect_dates_via_reference(
            self, reference: Database, tag_ref, refs_tag_date):
        refs = fetch_all_pages_of_relation(self.row, reference, tag_ref)
        dates = []
        for ref in refs:
            new_tars = fetch_all_pages_of_relation(ref, self.dates, refs_tag_date)
            dates.extend(new_tars)
        for date_row in dates:
            self.update_earliest_by_date_row(date_row)

    def update_earliest_by_date_row(self, date_row: PageRow):
        date_val = date_row.read_tag('dateval_manual')
        if self.earliest_date_val is None or date_row < self.earliest_date_val:
            self.earliest_date_row = date_row
            self.earliest_date_val = date_val


class GetterByReference(RowFunction):
    def __init__(self, dates: Database, arg: ReferenceArgument):
        self.dates = dates
        self.arg = arg

    def __call__(self, row: PageRow):
        if ref := fetch_unique_page_of_relation(row, self.arg.reference, self.arg.tag_ref):
            if tar := fetch_unique_page_of_relation(ref, self.dates, self.arg.refs_tag_date):
                return tar
            return None

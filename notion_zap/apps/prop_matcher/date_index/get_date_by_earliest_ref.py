from __future__ import annotations
from typing import Optional

from notion_zap.cli.editors import Database, PageRow
from notion_zap.apps.prop_matcher.struct import MainEditor, EditorBase
from notion_zap.apps.prop_matcher.common import \
    has_value, set_value, ReferenceInfo, get_all_pages_from_relation
from notion_zap.cli.structs import DateObject


class DateMatcherByEarliestRef(MainEditor):
    def __init__(self, bs: EditorBase):
        super().__init__(bs)
        self.no_replace = True

    def __call__(self):
        for table, tag_date, ref_args in self.args:
            get_date = GetterByEarliestRef(self.bs.dates, ref_args)
            for row in table.rows:
                if self.no_replace and has_value(row, tag_date):
                    continue
                if date := get_date(row):
                    set_value(row, date, tag_date)
                    self.reset_period(row)

    @staticmethod
    def reset_period(row: PageRow):
        row.write_relation(key_alias='periods', value=[])

    @property
    def args(self):
        return [
            (self.bs.readings, 'dates_begin',
             [ReferenceInfo(self.bs.checks, 'checks', 'dates')])
        ]


class GetterByEarliestRef:
    def __init__(self, dates: Database, ref_infos: list[ReferenceInfo]):
        self.dates = dates
        self.ref_infos = ref_infos

    def __call__(self, row: PageRow):
        collector = EarliestDateFinder(row, self.dates)
        for ref_info in self.ref_infos:
            collector.collect_dates_via_reference(ref_info)
        return collector.earliest_date_row


class EarliestDateFinder:
    def __init__(self, row: PageRow, dates: Database):
        self.row = row
        self.dates = dates
        self.earliest_date_row: Optional[PageRow] = None
        self.earliest_date_val = None

    def collect_dates_via_reference(self, ref_info: ReferenceInfo):
        refs = get_all_pages_from_relation(self.row, ref_info.reference, ref_info.tag_ref)
        dates = []
        for ref in refs:
            new_dates = get_all_pages_from_relation(
                ref, self.dates, ref_info.refs_tag_tar)
            dates.extend(new_dates)
        for date_row in dates:
            self.update_earliest_by_date_row(date_row)

    def update_earliest_by_date_row(self, date_row: PageRow):
        date_object: DateObject = date_row.read_tag('dateval_manual')
        date_val = date_object.start_date
        if self.earliest_date_val is None or date_val < self.earliest_date_val:
            self.earliest_date_row = date_row
            self.earliest_date_val = date_val

from __future__ import annotations

# from functools import reduce

from notion_zap.apps.prop_matcher.modules import *
from notion_zap.apps.prop_matcher.common.struct import TableModule, EditorBase
from notion_zap.apps.prop_matcher.modules.calendar import (
    DateTargetFiller, PeriodTargetFiller)
from notion_zap.cli import editors


class RegularMatchController:
    def __init__(self):
        self.bs = RegularEditorBase()
        self.agents: list[TableModule] = [
            SelfMatcher(self.bs),

            DateofDoublyLinked(self.bs),
            TableDateofReference(self.bs),
            DateMatcherofWritings(self.bs),
            DateMatcherofReadings(self.bs),
            DateTargetFiller(self.bs, False),

            PeriodMatcherofDates(self.bs),
            PeriodMatcherofDoublyLinked(self.bs),
            PeriodMatcherDefault(self.bs),
            PeriodMatcherReadingCreated(self.bs),
            PeriodTargetFiller(self.bs, False)


            # GcaltoScheduleMatcher(self.bs),
            # GcalfromScheduleMatcher(self.bs),
        ]

    def execute(self, request_size=0):
        self.bs.fetch(request_size)
        for agent in self.agents:
            agent()
        self.bs.save()


class RegularEditorBase(EditorBase):
    def __init__(self):
        super().__init__()
        self.root.exclude_archived = True
        # self.root.print_request_formats = True

    def fetch(self, request_size=0):
        for domain in self.root.aliased_blocks:
            self.fetch_one(domain, request_size)

    def fetch_one(self, domain: editors.Database, request_size):
        if domain is self.channels:
            return

        query = domain.rows.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        # OR clauses
        for tag in ['itself', 'periods', 'dates']:
            try:
                ft |= manager.relation(tag).is_empty()
            except KeyError:
                pass

        # OR clauses
        if domain is self.dates:
            manual_date = manager.date('manual_date')
            ft |= manual_date.is_empty()
            # sync_needed = manager.checkbox('sync_status').is_empty()
            # before_today = manual_date.on_or_before(dt.date.today())
            # ft |= (sync_needed & before_today)
        if domain in [self.journals, self.schedules]:
            # TODO : gcal_sync_status
            ft |= manager.relation('periods_created').is_empty()
            ft |= manager.relation('dates_created').is_empty()
        if domain is self.readings:
            ft |= manager.select('media_type').is_empty()

        # AND clauses
        if domain is self.readings:
            ft |= manager.relation('periods_created').is_empty()
            ft |= manager.relation('dates_created').is_empty()
            # ft &= manager.checkbox('no_exp').is_empty()
            # is_not_book = manager.checkbox('is_book').is_empty()
            # has_refs = reduce(
            #     lambda a, b: a | b,
            #     [manager.relation(tag).is_not_empty()
            #      for tag in ['journals', 'schedules']]
            # )
            # ft &= (is_not_book | has_refs)

        # ft.preview()
        query.push_filter(ft)
        query.execute(request_size)


if __name__ == '__main__':
    RegularMatchController().execute(request_size=20)

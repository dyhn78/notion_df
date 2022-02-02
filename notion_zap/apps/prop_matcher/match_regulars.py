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

            DateTargetFiller(self.bs, False),
            DateofDoublyLinked(self.bs),
            TableDateofReference(self.bs),
            DateMatcherofWritings(self.bs),
            DateMatcherofReadings(self.bs),

            PeriodTargetFiller(self.bs, False),
            PeriodMatcherofDates(self.bs),
            PeriodMatcherofDoublyLinked(self.bs),
            PeriodMatcherDefault(self.bs),
            ReadingsPeriodsCreated(self.bs),

            ReadingsMediaType(self.bs),
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
        if domain is not self.readings:
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
        if domain in [self.checks, self.journals]:
            # TODO : gcal_sync_status
            ft |= manager.relation('periods_created').is_empty()
            ft |= manager.relation('dates_created').is_empty()
        if domain is self.readings:
            ft |= manager.relation('itself').is_empty()

            ft |= manager.relation('periods_created').is_empty()
            ft |= manager.relation('dates_created').is_empty()
            ft |= manager.select('media_type').is_empty()

            begin = manager.relation('periods_begin').is_empty()
            begin &= manager.checkbox('no_exp').is_empty()
            ft |= begin

            begin = manager.relation('dates_begin').is_empty()
            begin &= manager.checkbox('no_exp').is_empty()
            ft |= begin

        # ft.preview()
        query.push_filter(ft)
        query.execute(request_size)


if __name__ == '__main__':
    RegularMatchController().execute(request_size=20)

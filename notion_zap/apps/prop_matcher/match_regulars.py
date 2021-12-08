from __future__ import annotations

from functools import reduce

from notion_zap.apps.prop_matcher.managers import *
from notion_zap.apps.prop_matcher.common.struct import EditorManager, EditorBase
from notion_zap.cli import editors


class RegularMatchController:
    def __init__(self, request_size=50):
        self.bs = RegularEditorBase(request_size)

    def execute(self):
        self.bs.fetch()
        agents: list[EditorManager] = [
            SelfMatcher(self.bs),

            DateMatcherofJournals(self.bs),
            DateMatcherofSchedules(self.bs),
            DateMatcherofMemos(self.bs),
            DateMatcherType1(self.bs),
            DateTargetFiller(self.bs, False),

            PeriodMatcherofDates(self.bs),
            PeriodMatcherofSchedules(self.bs),
            PeriodMatcherType1(self.bs),

            ProgressMatcherofWritings(self.bs),
            ProgressMatcherofDates(self.bs),

            # GcaltoScheduleMatcher(self.bs),
            # GcalfromScheduleMatcher(self.bs),
        ]
        for agent in agents:
            agent.execute()
        self.bs.save()


class RegularEditorBase(EditorBase):
    def __init__(self, request_size: int):
        super().__init__()
        self.request_size = request_size
        self.root.exclude_archived = True

    def fetch(self):
        for domain in self.root.aliased_blocks:
            self.fetch_one(domain)

    def fetch_one(self, domain: editors.Database):
        if domain is self.channels:
            return

        query = domain.rows.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        # OR clauses
        for tag in ['to_itself', 'to_periods', 'to_dates']:
            try:
                ft |= manager.relation(tag).is_empty()
            except KeyError:
                pass

        # OR clauses
        if domain is self.dates:
            sync_needed = manager.checkbox('sync_status').is_empty()
            manual_date = manager.date('manual_date')
            before_today = manual_date.on_or_before(dt.date.today())
            ft |= (sync_needed & before_today)
            ft |= manual_date.is_empty()
        if domain is self.schedules:
            # TODO : gcal_sync_status
            ft |= manager.relation('to_scheduled_periods').is_empty()
            ft |= manager.relation('to_scheduled_dates').is_empty()
            ft |= manager.relation('to_created_periods').is_empty()
            ft |= manager.relation('to_created_dates').is_empty()
        if domain is self.readings:
            ft |= manager.select('media_type').is_empty()

        # AND clauses
        if domain is self.readings:
            ft &= manager.checkbox('no_exp').is_empty()
            is_not_book = manager.checkbox('is_book').is_empty()
            has_refs = reduce(
                lambda a, b: a | b,
                [manager.relation(tag).is_not_empty()
                 for tag in ['to_journals', 'to_schedules']]
            )
            ft &= (is_not_book | has_refs)

        # ft.preview()
        query.push_filter(ft)
        query.execute(self.request_size, print_heads=5)


if __name__ == '__main__':
    RegularMatchController(request_size=20).execute()

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
            DateMatcherType1(self.bs),
            DateMatcherType2(self.bs),
            DateMatcherType3(self.bs),
            DateMatcherType4(self.bs),
            DateTargetFiller(self.bs, False),
            PeriodMatcherType1(self.bs),
            PeriodMatcherType2(self.bs),
            PeriodMatcherType3(self.bs),
            ProgressMatcherType1(self.bs),
            ProgressMatcherType2(self.bs),
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
        query = domain.rows.open_query()
        manager = query.filter_manager
        ft = query.open_filter()

        # OR clauses
        ft |= manager.relation_at('to_itself').is_empty()
        if domain is self.schedules:
            ft |= manager.relation_at('to_scheduled_periods').is_empty()
            ft |= manager.relation_at('to_scheduled_dates').is_empty()
            ft |= manager.relation_at('to_created_periods').is_empty()
            ft |= manager.relation_at('to_created_dates').is_empty()
            # TODO : gcal_sync_status
        else:
            if domain is self.dates:
                sync_needed = manager.checkbox_at('sync_status').is_empty()
                maker = manager.date_at('manual_date')
                before_today = maker.on_or_before(dt.date.today())
                ft |= (sync_needed & before_today)
                date_empty = maker.is_empty()
                ft |= date_empty
            if domain is not self.periods:
                ft |= manager.relation_at('to_periods').is_empty()
            if domain not in [self.periods, self.dates]:
                ft |= manager.relation_at('to_dates').is_empty()

        # AND clauses
        if domain is self.readings:
            ft &= manager.checkbox_at('no_exp').is_empty()
            is_not_book = manager.checkbox_at('is_book').is_empty()
            has_refs = reduce(
                lambda a, b: a | b,
                [manager.relation_at(tag).is_not_empty()
                 for tag in ['to_journals', 'to_schedules']]
            )
            ft &= (is_not_book | has_refs)
            # ft.preview()

        query.push_filter(ft)
        query.execute(self.request_size, print_heads=5)

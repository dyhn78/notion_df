from __future__ import annotations

from functools import reduce

from .routines import *
from .common.struct import RoutineManager, RootManager
from ...cli import editors


class RegularMatchController:
    def __init__(self, request_size=50):
        self.bs = RegularRootManager(request_size)

    def execute(self):
        self.bs.fetch()
        agents: list[RoutineManager] = [
            SelfMatcher(self.bs),
            DateMatcherType1(self.bs),
            DateMatcherType2(self.bs),
            DateMatcherType3(self.bs),
            DateMatcherType4(self.bs),
            DateTargetFiller(self.bs, True),
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


class RegularRootManager(RootManager):
    def __init__(self, request_size: int):
        super().__init__()
        self.request_size = request_size
        self.root.exclude_archived = True

    def fetch(self):
        for domain in self.root.databases:
            self.fetch_one(domain)

    def fetch_one(self, domain: editors.Database):
        query = domain.pages.open_query()
        maker = query.filter_maker
        ft = query.open_filter()

        # OR clauses
        ft |= maker.relation_at('to_itself').is_empty()
        if domain is self.schedules:
            ft |= maker.relation_at('to_scheduled_periods').is_empty()
            ft |= maker.relation_at('to_scheduled_dates').is_empty()
            ft |= maker.relation_at('to_created_periods').is_empty()
            ft |= maker.relation_at('to_created_dates').is_empty()
            # TODO : gcal_sync_status
        else:
            if domain is self.dates:
                sync_needed = maker.checkbox_at('sync_status').is_empty()
                before_today = maker.date_at('manual_date').on_or_before(dt.date.today())
                ft |= (sync_needed & before_today)
            if domain is not self.periods:
                ft |= maker.relation_at('to_periods').is_empty()
            if domain not in [self.periods, self.dates]:
                ft |= maker.relation_at('to_dates').is_empty()

        # AND clauses
        if domain is self.readings:
            ft &= maker.checkbox_at('status_exclude').is_empty()
            is_not_book = maker.checkbox_at('is_book').is_empty()
            has_refs = reduce(
                lambda a, b: a | b,
                [maker.relation_at(tag).is_not_empty()
                 for tag in ['to_journals', 'to_schedules']]
            )
            ft &= (is_not_book | has_refs)
            # ft.preview()

        query.push_filter(ft)
        # query.preview()
        query.execute(self.request_size, print_heads=5)

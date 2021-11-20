from __future__ import annotations

from functools import reduce

from .matchers import *
from .common.struct import Matcher, LocalBase
from ...cli import editors


class RegularMatchController:
    def __init__(self, date_range=0):
        self.bs = RegularLocalBase()
        self.date_range = date_range

    def execute(self):
        self.bs.fetch()
        agents_1: list[Matcher] = [
            SelfMatcher(self.bs),
            DateMatcherType1(self.bs),
            DateMatcherType2(self.bs),
            DateMatcherType3(self.bs),
            DateMatcherType4(self.bs),
            PeriodMatcherType1(self.bs),
            PeriodMatcherType2(self.bs),
            PeriodMatcherType3(self.bs),
            ProgressMatcherType1(self.bs),
            ProgressMatcherType2(self.bs),
        ]
        for agent in agents_1:
            agent.execute()
        self.bs.save()

        # self.bs.fetch(self.bs.readings)
        # agents_2: list[Matcher] = [
        #     DateMatcherType4(self.bs)
        # ]
        # for agent in agents_2:
        #     agent.execute()
        # self.bs.save()


class RegularLocalBase(LocalBase):
    MAX_REQUEST_SIZE = 50

    def __init__(self):
        super().__init__()
        self.root.exclude_archived = True

    def fetch(self):
        for database in self.root.databases:
            domain = database.pagelist
            self.fetch_one(domain)

    def fetch_one(self, domain: editors.PageList):
        query = domain.open_query()
        maker = query.filter_maker
        ft = query.open_filter()

        # OR clauses
        ft |= maker.relation_at('to_itself').is_empty()
        if domain is not self.periods:
            ft |= maker.relation_at('to_periods').is_empty()
        if domain not in [self.periods, self.dates]:
            ft |= maker.relation_at('to_dates').is_empty()
        if domain is self.dates:
            sync_needed = maker.checkbox_at('sync_status').is_empty()
            before_today = maker.date_at('manual_date').on_or_before(dt.date.today())
            ft |= (sync_needed & before_today)
        if domain is self.schedules:
            ft |= maker.relation_at('to_scheduled_periods').is_empty()
            ft |= maker.relation_at('to_scheduled_dates').is_empty()

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
        query.execute(self.MAX_REQUEST_SIZE)

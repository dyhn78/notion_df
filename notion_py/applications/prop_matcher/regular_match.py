from __future__ import annotations

from .matchers import *
from .common.struct import Matcher, LocalBase


class MatchController:
    def __init__(self, date_range=0):
        self.bs = RegularLocalBase()
        self.date_range = date_range

    def execute(self):
        self.bs.fetch()
        # self.bs.fetch(self.date_range)
        agents: list[Matcher] = [
            SelfMatcher(self.bs),
            DateMatcherType1(self.bs),
            DateMatcherType2(self.bs),
            PeriodMatcherType1(self.bs),
            PeriodMatcherType2(self.bs),
            ProjectMatcher(self.bs),
        ]
        for agent in agents:
            agent.execute()
        self.bs.save()


class RegularLocalBase(LocalBase):
    MAX_REQUEST_SIZE = 100

    def __init__(self):
        super().__init__()
        self.root.exclude_archived = True

    def fetch(self):
        # for pagelist in [self.periods, self.dates]:
        #     query_within_date_range(pagelist, 'index_as_domain', date_range)
        for pagelist in [self.dates]:
            query = pagelist.open_query()
            frame = query.filter_maker.relation_at('to_periods')
            ft = frame.is_empty()
            frame = query.filter_maker.relation_at('to_itself')
            ft |= frame.is_empty()
            query.push_filter(ft)
            query.execute(self.MAX_REQUEST_SIZE)
        for pagelist in [self.journals, self.memos, self.writings]:
            query = pagelist.open_query()
            frame = query.filter_maker.relation_at('to_periods')
            ft = frame.is_empty()
            frame = query.filter_maker.relation_at('to_dates')
            ft |= frame.is_empty()
            frame = query.filter_maker.relation_at('to_itself')
            ft |= frame.is_empty()
            query.push_filter(ft)
            query.execute(self.MAX_REQUEST_SIZE)

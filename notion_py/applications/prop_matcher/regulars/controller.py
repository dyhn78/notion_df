from __future__ import annotations

from .match_to_dates import DateMatcherType1, DateMatcherType2
from .match_to_itself import MatchertoItself
from .match_to_periods import PeriodMatcherType1, PeriodMatcherType2
from ..common.base import Matcher, LocalBase


class MatchController:
    def __init__(self, date_range=0):
        self.bs = RegularLocalBase()
        self.date_range = date_range

    def execute(self):
        self.bs.fetch(self.date_range)
        agents: list[Matcher] = [
            MatchertoItself(self.bs),
            DateMatcherType1(self.bs),
            DateMatcherType2(self.bs),
            PeriodMatcherType1(self.bs),
            PeriodMatcherType2(self.bs)
        ]
        for agent in agents:
            agent.execute()
        self.bs.save()


class RegularLocalBase(LocalBase):
    MAX_REQUEST_SIZE = 100

    def fetch(self, date_range: int):
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

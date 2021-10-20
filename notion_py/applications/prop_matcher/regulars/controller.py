from __future__ import annotations

from .base import LocalBase, Matcher
from .match_to_itself import MatchertoItself
from .match_to_dates import DateMatcherType1, DateMatcherType2
from .match_to_periods import PeriodMatcherType1, PeriodMatcherType2


class MatchController:
    def __init__(self, date_range=0):
        self.bs = LocalBase(date_range)
        self.bs.fetch()
        self.agents: list[Matcher] = [
            MatchertoItself(self.bs),
            DateMatcherType1(self.bs),
            DateMatcherType2(self.bs),
            PeriodMatcherType1(self.bs),
            PeriodMatcherType2(self.bs)
        ]

    def execute(self):
        for agent in self.agents:
            agent.execute()
        self.bs.apply_results()

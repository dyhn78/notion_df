from __future__ import annotations

from .struct import LocalBase, Matcher
from .match_to_times import MatchertoDates, MatchertoPeriods
from .match_to_itself import MatchertoItself


class MatchController:
    def __init__(self, date_range=0):
        self.bs = LocalBase(date_range)

        self.agents: list[Matcher] = [
            MatchertoItself(self.bs),
            MatchertoDates(self.bs),
            MatchertoPeriods(self.bs)
        ]

    def execute(self):
        self.bs.fetch()
        for agent in self.agents:
            agent.execute()
        self.bs.apply_results()

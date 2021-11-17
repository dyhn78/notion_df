from __future__ import annotations

from .matchers import *
from .common.base import Matcher, LocalBase
from ...cli import editors


class MatchController:
    def __init__(self, date_range=0):
        self.bs = RegularLocalBase()
        self.date_range = date_range

    def execute(self):
        self.bs.fetch_all()
        agents_1: list[Matcher] = [
            SelfMatcher(self.bs),
            DateMatcherType1(self.bs),
            DateMatcherType2(self.bs),
            DateMatcherType3(self.bs),
            PeriodMatcherType1(self.bs),
            PeriodMatcherType2(self.bs),
            ProjectMatcher(self.bs),
        ]
        for agent in agents_1:
            agent.execute()
        self.bs.save()

        # self.bs.fetch(self.bs.readings)
        # agents_2: list[Matcher] = [
        #     DateMatcherType3(self.bs)
        # ]
        # for agent in agents_2:
        #     agent.execute()
        # self.bs.save()


class RegularLocalBase(LocalBase):
    MAX_REQUEST_SIZE = 50

    def __init__(self):
        super().__init__()
        self.root.exclude_archived = True

    def fetch_all(self):
        for database in self.root.databases:
            pagelist = database.pagelist
            self.fetch(pagelist)

    def fetch(self, pagelist: editors.PageList):
        query = pagelist.open_query()
        ft = query.open_filter()
        frame = query.filter_maker.relation_at('to_itself')
        ft |= frame.is_empty()
        if pagelist is not self.periods:
            frame = query.filter_maker.relation_at('to_periods')
            ft |= frame.is_empty()
        if pagelist not in [self.periods, self.dates]:
            frame = query.filter_maker.relation_at('to_dates')
            ft |= frame.is_empty()
        if pagelist is self.readings:
            frame = query.filter_maker.checkbox_at('status_exclude')
            ft &= frame.is_empty()
        query.push_filter(ft)
        query.execute(self.MAX_REQUEST_SIZE)

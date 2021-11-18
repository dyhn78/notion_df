from __future__ import annotations

from .matchers import *
from .common.base import Matcher, LocalBase
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
            PeriodMatcherType1(self.bs),
            PeriodMatcherType2(self.bs),
            ProgressMatcherType1(self.bs),
            ProgressMatcherType2(self.bs),
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

    def fetch(self):
        for database in self.root.databases:
            pagelist = database.pagelist
            self.fetch_one(pagelist)

    def fetch_one(self, pagelist: editors.PageList):
        query = pagelist.open_query()
        maker = query.filter_maker
        ft = query.open_filter()

        # OR clauses
        frame = maker.relation_at('to_itself')
        ft |= frame.is_empty()
        if pagelist is not self.periods:
            frame = maker.relation_at('to_periods')
            ft |= frame.is_empty()
        if pagelist not in [self.periods, self.dates]:
            frame = maker.relation_at('to_dates')
            ft |= frame.is_empty()
        if pagelist is self.dates:
            frame_sync = maker.checkbox_at('sync_status')
            ft_sync = frame_sync.is_empty()
            frame_date = maker.date_at('manual_date')
            ft_date = frame_date.on_or_before(dt.date.today())
            ft |= (ft_sync & ft_date)

        # AND clauses
        if pagelist is self.readings:
            frame = maker.checkbox_at('status_exclude')
            ft &= frame.is_empty()

        query.push_filter(ft)
        # query.preview()
        query.execute(self.MAX_REQUEST_SIZE)

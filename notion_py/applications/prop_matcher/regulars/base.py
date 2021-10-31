from __future__ import annotations

from abc import ABC, abstractmethod

from notion_py.interface import RootEditor
from ..common.query_maker import query_within_date_range
from ..frame import MatchFrames
from ...database_info import DatabaseInfo


class Matcher(ABC):
    def __init__(self, bs: LocalBase):
        self.bs = bs

    @abstractmethod
    def execute(self):
        pass


class LocalBase:
    def __init__(self, date_range: int):
        self.root = RootEditor()
        self.date_range = date_range
        self.periods = self.root.open_pagelist(*DatabaseInfo.PERIODS,
                                               frame=MatchFrames.PERIODS)
        self.dates = self.root.open_pagelist(*DatabaseInfo.DATES,
                                             frame=MatchFrames.DATES)
        self.journals = self.root.open_pagelist(*DatabaseInfo.JOURNALS,
                                                frame=MatchFrames.JOURNALS)
        self.memos = self.root.open_pagelist(*DatabaseInfo.MEMOS,
                                             frame=MatchFrames.MEMOS)
        self.writings = self.root.open_pagelist(*DatabaseInfo.WRITINGS,
                                                frame=MatchFrames.WRITINGS)

    def fetch(self):
        for pagelist in [self.periods, self.dates]:
            query_within_date_range(pagelist, 'index_as_domain', self.date_range)
        for pagelist in [self.journals, self.memos, self.writings]:
            query = pagelist.open_query()
            frame = query.make_filter.relation_at('to_periods')
            ft = frame.is_empty()
            frame = query.make_filter.relation_at('to_dates')
            ft &= frame.is_empty()
            query.push_filter(ft)
            query.execute()

    def apply_results(self):
        self.root.save()

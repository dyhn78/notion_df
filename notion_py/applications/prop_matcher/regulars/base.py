from __future__ import annotations
from abc import ABC, abstractmethod

from ..common.query_maker import QueryMaker
from ..frame import MatchFrames
from ...database_info import DatabaseInfo
from notion_py.interface import RootEditor


class Matcher(ABC):
    def __init__(self, bs: LocalBase):
        self.bs = bs

    @abstractmethod
    def execute(self):
        pass


class LocalBase:
    def __init__(self, date_range: int):
        self.root = RootEditor()
        self.query_maker = QueryMaker(date_range)
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
        for pagelist in [self.periods, self.dates, self.journals]:
            self.query_maker.query_as_parents(pagelist, 'index_as_domain')
        for pagelist in [self.memos, self.writings]:
            self.query_maker.query_as_parents(pagelist, 'index_as_domain')

    def apply_results(self):
        for pagelist in [self.periods, self.dates, self.journals, self.memos,
                         self.writings]:
            pagelist.execute()

from __future__ import annotations
from abc import ABC, abstractmethod

from notion_py.applications.database_info import DatabaseInfo
from notion_py.applications.prop_matcher.common.frame import MatchFrames
from notion_py.interface import RootEditor


class Matcher(ABC):
    def __init__(self, bs: LocalBase):
        self.bs = bs

    @abstractmethod
    def execute(self):
        pass


class LocalBase:
    def __init__(self):
        self.root = RootEditor()
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

    def save(self):
        self.root.save()

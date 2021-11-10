from __future__ import annotations
from abc import ABC, abstractmethod

from notion_py.applications.database_info import DatabaseInfo
from notion_py.applications.prop_matcher.common.frame import MatchFrames
from notion_py.interface import editor


class Matcher(ABC):
    def __init__(self, bs: LocalBase):
        self.bs = bs

    @abstractmethod
    def execute(self):
        pass


class LocalBase:
    def __init__(self):
        self.root = editor.RootEditor()
        self.periods = self.root.open_database(*DatabaseInfo.PERIODS,
                                               frame=MatchFrames.PERIODS).pagelist
        self.dates = self.root.open_database(*DatabaseInfo.DATES,
                                             frame=MatchFrames.DATES).pagelist
        self.journals = self.root.open_database(*DatabaseInfo.JOURNALS,
                                                frame=MatchFrames.JOURNALS).pagelist
        self.memos = self.root.open_database(*DatabaseInfo.MEMOS,
                                             frame=MatchFrames.MEMOS).pagelist
        self.writings = self.root.open_database(*DatabaseInfo.WRITINGS,
                                                frame=MatchFrames.WRITINGS).pagelist

    def save(self):
        self.root.save()

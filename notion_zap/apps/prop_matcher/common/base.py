from __future__ import annotations
from abc import ABC, abstractmethod

from notion_zap.apps.config.common import DatabaseInfo
from notion_zap.apps.config.prop_matcher import MatchFrames
from notion_zap.cli import editors


class Matcher(ABC):
    def __init__(self, bs: LocalBase):
        self.bs = bs

    @abstractmethod
    def execute(self):
        pass


class LocalBase:
    def __init__(self):
        self.root = editors.RootEditor()
        self.periods = self.root.open_database(*DatabaseInfo.PERIODS,
                                               frame=MatchFrames.PERIODS).pagelist
        self.dates = self.root.open_database(*DatabaseInfo.DATES,
                                             frame=MatchFrames.DATES).pagelist
        self.journals = self.root.open_database(*DatabaseInfo.JOURNALS,
                                                frame=MatchFrames.JOURNALS).pagelist
        self.writings = self.root.open_database(*DatabaseInfo.WRITINGS,
                                                frame=MatchFrames.WRITINGS).pagelist
        self.memos = self.root.open_database(*DatabaseInfo.MEMOS,
                                             frame=MatchFrames.MEMOS).pagelist
        self.schedules = self.root.open_database(*DatabaseInfo.SCHEDULES,
                                                 frame=MatchFrames.SCHEDULES).pagelist
        self.readings = self.root.open_database(*DatabaseInfo.READINGS,
                                                frame=MatchFrames.READINGS).pagelist

    def save(self):
        self.root.save()

from __future__ import annotations
from abc import ABC, abstractmethod


from notion_zap.apps.config.common import DatabaseInfo
from notion_zap.apps.config.prop_matcher import MatchFrames
from notion_zap.cli import editors


class EditorBase:
    def __init__(self):
        self.root = editors.Root()
        self.periods = self.root.open_database(*DatabaseInfo.PERIODS,
                                               frame=MatchFrames.PERIODS)
        self.dates = self.root.open_database(*DatabaseInfo.DATES,
                                             frame=MatchFrames.DATES)
        self.journals = self.root.open_database(*DatabaseInfo.JOURNALS,
                                                frame=MatchFrames.JOURNALS)
        self.writings = self.root.open_database(*DatabaseInfo.WRITINGS,
                                                frame=MatchFrames.WRITINGS)
        self.memos = self.root.open_database(*DatabaseInfo.MEMOS,
                                             frame=MatchFrames.MEMOS)
        self.schedules = self.root.open_database(*DatabaseInfo.SCHEDULES,
                                                 frame=MatchFrames.SCHEDULES)
        self.readings = self.root.open_database(*DatabaseInfo.READINGS,
                                                frame=MatchFrames.READINGS)

    def save(self):
        self.root.save()


class EditorManager(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs

    @abstractmethod
    def execute(self):
        pass

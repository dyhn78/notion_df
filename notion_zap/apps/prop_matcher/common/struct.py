from __future__ import annotations
from abc import ABC, abstractmethod

from notion_zap.apps.config.common import DatabaseInfo
from notion_zap.apps.config.prop_matcher import MatchFrames
from notion_zap.cli import editors


class EditorBase:
    def __init__(self):
        self.root = editors.Root()
        self.periods = self.root.objects.database(*DatabaseInfo.PERIODS,
                                                  frame=MatchFrames.PERIODS)
        self.dates = self.root.objects.database(*DatabaseInfo.DATES,
                                                frame=MatchFrames.DATES)
        self.marks = self.root.objects.database(*DatabaseInfo.MARKS,
                                                frame=MatchFrames.MARKS)
        self.journals = self.root.objects.database(*DatabaseInfo.JOURNALS,
                                                   frame=MatchFrames.JOURNALS)
        self.tasks = self.root.objects.database(*DatabaseInfo.TASKS,
                                                frame=MatchFrames.TASKS)
        self.schedules = self.root.objects.database(*DatabaseInfo.SCHEDULES,
                                                    frame=MatchFrames.SCHEDULES)
        self.readings = self.root.objects.database(*DatabaseInfo.READINGS,
                                                   frame=MatchFrames.READINGS)
        self.channels = self.root.objects.database(*DatabaseInfo.CHANNELS,
                                                   frame=MatchFrames.CHANNELS)

    def save(self):
        self.root.save()


class EditorManager(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs

    @abstractmethod
    def execute(self):
        pass

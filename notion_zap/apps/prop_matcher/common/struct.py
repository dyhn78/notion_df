from __future__ import annotations
from abc import ABC, abstractmethod

from notion_zap.apps.config import DatabaseInfo
from notion_zap.apps.prop_matcher.config import MatchFrames
from notion_zap.cli import editors
from notion_zap.cli.editors import PageRow


class EditorBase:
    def __init__(self):
        self.root = editors.Root(print_heads=5)
        self.periods = self.root.objects.database(*DatabaseInfo.PERIODS,
                                                  frame=MatchFrames.PERIODS)
        self.dates = self.root.objects.database(*DatabaseInfo.DATES,
                                                frame=MatchFrames.DATES)
        self.journals = self.root.objects.database(*DatabaseInfo.JOURNALS,
                                                   frame=MatchFrames.JOURNALS)
        self.writings = self.root.objects.database(*DatabaseInfo.WRITINGS,
                                                   frame=MatchFrames.WRITINGS)
        self.schedules = self.root.objects.database(*DatabaseInfo.SCHEDULES,
                                                    frame=MatchFrames.SCHEDULES)
        self.tasks = self.root.objects.database(*DatabaseInfo.TASKS,
                                                frame=MatchFrames.TASKS)
        self.channels = self.root.objects.database(*DatabaseInfo.CHANNELS,
                                                   frame=MatchFrames.CHANNELS)
        self.readings = self.root.objects.database(*DatabaseInfo.READINGS,
                                                   frame=MatchFrames.READINGS)

    def save(self):
        self.root.save()


class EditorModule(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs


class TableModule(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs

    @abstractmethod
    def __call__(self):
        pass

class RowModule(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs

    @abstractmethod
    def __call__(self, dom: PageRow):
        pass

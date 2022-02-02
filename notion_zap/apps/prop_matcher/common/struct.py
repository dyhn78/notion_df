from __future__ import annotations
from abc import ABC, abstractmethod

from notion_zap.apps.config import DatabaseInfo
from notion_zap.apps.prop_matcher.config import MatchFrames
from notion_zap.cli.editors import PageRow, Root


class EditorBase:
    def __init__(self, print_heads=5, print_request_formats=False):
        self.root = Root(print_response_heads=print_heads,
                         print_request_formats=print_request_formats)
        self.periods = self.root.objects.database(*DatabaseInfo.PERIODS,
                                                  frame=MatchFrames.PERIODS)
        self.dates = self.root.objects.database(*DatabaseInfo.DATES,
                                                frame=MatchFrames.DATES)
        self.journals = self.root.objects.database(*DatabaseInfo.JOURNALS,
                                                   frame=MatchFrames.JOURNALS)
        self.checks = self.root.objects.database(*DatabaseInfo.CHECKS,
                                                 frame=MatchFrames.CHECKS)
        self.writings = self.root.objects.database(*DatabaseInfo.WRITINGS,
                                                   frame=MatchFrames.WRITINGS)
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

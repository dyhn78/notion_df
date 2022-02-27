from __future__ import annotations
from abc import ABC, abstractmethod

from notion_zap.apps.config import DatabaseInfo
from notion_zap.apps.prop_matcher.config import Frames
from notion_zap.cli.editors import PageRow, Root, Database


class EditorBase:
    def __init__(self, print_heads=5, print_request_formats=False):
        self.root = Root(print_response_heads=print_heads,
                         print_request_formats=print_request_formats)
        self.periods = self.root.objects.database(*DatabaseInfo.PERIODS,
                                                  frame=Frames.PERIODS)
        self.dates = self.root.objects.database(*DatabaseInfo.DATES,
                                                frame=Frames.DATES)

        self.journals = self.root.objects.database(*DatabaseInfo.JOURNALS,
                                                   frame=Frames.JOURNALS)
        self.checks = self.root.objects.database(*DatabaseInfo.CHECKS,
                                                 frame=Frames.CHECKS)
        self.topics = self.root.objects.database(*DatabaseInfo.TOPICS,
                                                 frame=Frames.TOPICS)
        self.writings = self.root.objects.database(*DatabaseInfo.WRITINGS,
                                                   frame=Frames.WRITINGS)
        self.tasks = self.root.objects.database(*DatabaseInfo.TASKS,
                                                frame=Frames.TASKS)

        self.projects = self.root.objects.database(*DatabaseInfo.PROJECTS,
                                                   frame=Frames.PROJECTS)
        self.channels = self.root.objects.database(*DatabaseInfo.CHANNELS,
                                                   frame=Frames.CHANNELS)
        self.readings = self.root.objects.database(*DatabaseInfo.READINGS,
                                                   frame=Frames.READINGS)

    def __open_database(self, info_tuple, frame):
        return self.root.objects.database(*info_tuple, frame=frame)

    def save(self):
        self.root.save()


class BaseEditor(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs


class MainEditor(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs

    @abstractmethod
    def __call__(self):
        pass


class RowEditor(ABC):
    @abstractmethod
    def __call__(self, row: PageRow):
        pass


class BasedRowProcessorDepr(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs

    @abstractmethod
    def __call__(self, row: PageRow):
        pass


class ModuleDepr(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs


class TableModuleDepr(ABC):
    def __init__(self, bs: EditorBase):
        self.bs = bs

    @abstractmethod
    def __call__(self):
        pass

from __future__ import annotations

from abc import ABC, abstractmethod

from notion_zap.apps.config import DatabaseInfo, BlockKey
from notion_zap.apps.prop_matcher.config import FramesDepr, Frames
from notion_zap.cli.editors import PageRow, Root


class MainEditor:
    def __init__(self, print_heads=5, print_request_formats=False):
        self.root = Root(print_response_heads=print_heads,
                         print_request_formats=print_request_formats)
        for key in BlockKey:
            key: BlockKey
            block = self.root.space.database(key.id_or_url, key, Frames[key])
            block.title = key.title


class MainEditorDepr:
    def __init__(self, print_heads=5, print_request_formats=False):
        self.root = Root(print_response_heads=print_heads,
                         print_request_formats=print_request_formats)
        self.periods = self.root.space.database_depr(*DatabaseInfo.PERIODS,
                                                     frame=FramesDepr.PERIODS)
        self.dates = self.root.space.database_depr(*DatabaseInfo.DATES,
                                                   frame=FramesDepr.DATES)

        self.journals = self.root.space.database_depr(*DatabaseInfo.JOURNALS,
                                                      frame=FramesDepr.JOURNALS)
        self.checks = self.root.space.database_depr(*DatabaseInfo.CHECKS,
                                                    frame=FramesDepr.CHECKS)
        self.topics = self.root.space.database_depr(*DatabaseInfo.TOPICS,
                                                    frame=FramesDepr.TOPICS)
        self.writings = self.root.space.database_depr(*DatabaseInfo.WRITINGS,
                                                      frame=FramesDepr.WRITINGS)
        self.tasks = self.root.space.database_depr(*DatabaseInfo.TASKS,
                                                   frame=FramesDepr.TASKS)

        self.projects = self.root.space.database_depr(*DatabaseInfo.PROJECTS,
                                                      frame=FramesDepr.PROJECTS)
        self.channels = self.root.space.database_depr(*DatabaseInfo.CHANNELS,
                                                      frame=FramesDepr.CHANNELS)
        self.readings = self.root.space.database_depr(*DatabaseInfo.READINGS,
                                                      frame=FramesDepr.READINGS)

    def __open_database(self, info_tuple, frame):
        return self.root.space.database_depr(*info_tuple, frame=frame)

    def save(self):
        self.root.save()


class Processor(ABC):
    def __init__(self, bs: MainEditorDepr):
        self.bs = bs

    @abstractmethod
    def __call__(self):
        pass


class RowHandler(ABC):
    @abstractmethod
    def __call__(self, row: PageRow):
        pass

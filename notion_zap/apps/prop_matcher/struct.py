from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Hashable, Union, Any

from notion_zap.apps.config import MyBlock, DatabaseInfoDepr
from notion_zap.apps.prop_matcher.config import FramesDepr, Frames
from notion_zap.cli.editors import PageRow, Root, Database


def init_root(print_heads=5, print_request_formats=False):
    root = Root(print_response_heads=print_heads,
                print_request_formats=print_request_formats)
    for bc in MyBlock:
        bc: MyBlock
        block = root.space.database(bc.id_or_url, bc, Frames[bc])
        block.title = bc.title
    return root


class MainEditorDepr:
    def __init__(self, print_heads=5, print_request_formats=False):
        self.root = Root(print_response_heads=print_heads,
                         print_request_formats=print_request_formats)
        self.weeks = self.root[MyBlock.weeks]
        self.dates = self.root.space.database_depr(*DatabaseInfoDepr.DATES,
                                                   frame=FramesDepr.DATES)

        self.journals = self.root.space.database_depr(*DatabaseInfoDepr.JOURNALS,
                                                      frame=FramesDepr.JOURNALS)
        self.checks = self.root.space.database_depr(*DatabaseInfoDepr.CHECKS,
                                                    frame=FramesDepr.CHECKS)
        self.topics = self.root.space.database_depr(*DatabaseInfoDepr.TOPICS,
                                                    frame=FramesDepr.TOPICS)
        self.writings = self.root.space.database_depr(*DatabaseInfoDepr.WRITINGS,
                                                      frame=FramesDepr.WRITINGS)
        self.tasks = self.root.space.database_depr(*DatabaseInfoDepr.TASKS,
                                                   frame=FramesDepr.TASKS)

        self.projects = self.root.space.database_depr(*DatabaseInfoDepr.PROJECTS,
                                                      frame=FramesDepr.PROJECTS)
        self.channels = self.root.space.database_depr(*DatabaseInfoDepr.CHANNELS,
                                                      frame=FramesDepr.CHANNELS)
        self.readings = self.root.space.database_depr(*DatabaseInfoDepr.READINGS,
                                                      frame=FramesDepr.READINGS)

    def __open_database(self, info_tuple, frame):
        return self.root.space.database_depr(*info_tuple, frame=frame)

    def save(self):
        self.root.save()


class Processor(ABC):
    def __init__(self, bs: MatchBase):
        self.bs = bs
        self.root = self.bs.root

    @abstractmethod
    def __call__(self):
        pass


class RowHandler(ABC):
    @abstractmethod
    def __call__(self, row: PageRow):
        pass


class MatchBase:
    def __init__(self, items: dict[MyBlock, set[Union[Hashable, tuple[Hashable, Any]]]]):
        self.root = init_root()
        self.root.exclude_archived = True
        self._options: dict[MyBlock] = {}
        for block_key, option_elements in items.items():
            block_option = self._options[block_key] = {}
            for element in option_elements:
                if isinstance(element, tuple):
                    option_key, option_value = element
                else:
                    option_key = element
                    option_value = None
                block_option[option_key] = option_value

    def get_block_option(self, key: Union[MyBlock, Hashable]):
        if not isinstance(key, MyBlock):
            key = MyBlock[key]
        return self._options[key]

    def keys(self):
        return self._options.keys()

    def pick(self, option_key: Hashable):
        for block_key, block_option in self._options.items():
            if option_key in block_option.keys():
                table: Database = self.root[option_key]
                yield block_key, table

    def filtered_pick(self, option_key: Hashable, option_value=None):
        for block_key, block_option in self._options.items():
            for _option_key, _option_value in block_option.items():
                if _option_key == option_key and _option_value == option_value:
                    table: Database = self.root[option_key]
                    yield block_key, table
                    continue

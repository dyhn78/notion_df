from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Hashable, Union, Any

from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.config import Frames
from notion_zap.cli.editors import PageRow, Root, Database


class MatchBase:
    def __init__(self, items: dict[MyBlock, set[Union[Hashable, tuple[Hashable, Any]]]] = None):
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
                table: Database = self.root[block_key]
                yield block_key, table

    def filtered_pick(self, option_key: Hashable, option_value=None):
        for block_key, block_option in self._options.items():
            for _option_key, _option_value in block_option.items():
                if _option_key == option_key and _option_value == option_value:
                    table: Database = self.root[block_key]
                    yield block_key, table
                    continue


def init_root(print_heads=5, print_request_formats=False):
    root = Root(print_response_heads=print_heads,
                print_request_formats=print_request_formats)
    for key in MyBlock:
        key: MyBlock
        block = root.space.database(key.id_or_url, key, Frames.get(key))
        block.title = key.title
    return root


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

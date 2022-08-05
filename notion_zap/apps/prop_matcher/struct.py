from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Hashable, Union, Any, Optional

from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.config import Frames
from notion_zap.cli.blocks import PageRow
from notion_zap.cli.core.base import Root


class MatchOptions:
    def __init__(self, options_input: dict[MyBlock, set[Union[Hashable, tuple[Hashable, Any]]]] =
    None):
        self.items: dict[MyBlock, dict[Hashable, Optional[Any]]] = {}
        for block_key, option_elements in options_input.items():
            block_option = self.items[block_key] = {}
            for element in option_elements:
                if isinstance(element, tuple):
                    option_key, option_value = element
                else:
                    option_key = element
                    option_value = None
                block_option[option_key] = option_value

    def __iter__(self):
        return iter(self.items.keys())

    def filter_key(self, option_key: Hashable) -> list[MyBlock]:
        res = []
        for block_key, block_option in self.items.items():
            if option_key in block_option.keys():
                res.append(block_key)
        return res

    def filter_pair(
            self, option_key: Hashable, option_value=None) -> list[MyBlock]:
        res = []
        for block_key, block_option in self.items.items():
            for _option_key, _option_value in block_option.items():
                if _option_key == option_key and _option_value == option_value:
                    res.append(block_key)
                    continue
        return res


def init_root(exclude_archived=True, print_heads=5, print_request_formats=False):
    root = Root(print_response_heads=print_heads,
                print_request_formats=print_request_formats,
                exclude_archived=exclude_archived)
    for key in MyBlock:
        key: MyBlock
        block = root.space.database(key.block_id, key, Frames.get(key))
        block.title = key.title
    return root


class BaseProcessor(ABC):
    def __init__(self, root: Root):
        self.root = root

    @abstractmethod
    def __call__(self):
        pass


class Processor(BaseProcessor, ABC):
    def __init__(self, root: Root, option: MatchOptions):
        super().__init__(root)
        self.option = option

    @abstractmethod
    def __call__(self):
        pass


class Saver(BaseProcessor):
    def __call__(self):
        self.root.save()


class RowHandler(ABC):
    @abstractmethod
    def __call__(self, row: PageRow):
        pass

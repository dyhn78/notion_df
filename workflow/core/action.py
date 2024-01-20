from __future__ import annotations

from abc import ABCMeta, abstractmethod
from itertools import chain
from typing import Iterable, Optional, Any, Iterator, TypeVar

from notion_df.entity import Page
from notion_df.util.misc import repr_object
from workflow.block_enum import exclude_template


class Action(metaclass=ABCMeta):
    def __repr__(self):
        return repr_object(self)

    def __init_subclass__(cls, **kwargs):
        cls.query_all = exclude_template(cls.query_all)

    @abstractmethod
    def query_all(self) -> Iterable[Page]:
        """full-scan mode"""
        pass

    @abstractmethod
    def filter(self, page: Page) -> bool:
        """from given retrieved pages regardless of `recent_pages` or `query_all()`,
        pick the ones which need to process."""
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]) -> Any:
        pass


class IterableAction(Action, metaclass=ABCMeta):
    def process(self, pages: Iterable[Page]):
        pages_it = peek(pages)
        if pages_it is None:
            return
        print(self)
        for page in pages_it:
            self.process_page(page)

    @abstractmethod
    def process_page(self, page: Page) -> Any:
        pass


T = TypeVar('T')


def peek(it: Iterable[T]) -> Optional[Iterator[T]]:
    it = iter(it)
    try:
        _first_element = next(it)
    except StopIteration:
        return None
    return chain([_first_element], it)

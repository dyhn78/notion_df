from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime
from itertools import chain
from pprint import pformat
from typing import Iterable, Optional, Any, Iterator, TypeVar, final
from uuid import UUID

from loguru import logger

from notion_df.entity import Page, search_by_title, Block
from notion_df.util.misc import repr_object
from notion_df.variable import print_width
from workflow.block_enum import is_template

log_page_id = '6d16dc6747394fca95dc169c8c736e2d'
log_page_block = Block(log_page_id)
log_date_format = '%Y-%m-%d %H:%M:%S+09:00'
log_date_group_format = '%Y-%m-%d'
log_last_success_time_parent_block = Block('c66d852e27e84d92b6203dfdadfefad8')

my_user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')


class Action(metaclass=ABCMeta):
    def __repr__(self):
        return repr_object(self)

    @abstractmethod
    def query_all(self) -> Iterable[Page]:
        """query the database - the result will go through _filter()."""
        pass

    @abstractmethod
    def _filter(self, page: Page) -> bool:
        """from given retrieved pages regardless of `recent_pages` or `query_all()`,
        pick the ones which need to process."""
        pass

    @final
    def filter(self, page: Page) -> bool:
        return self._filter(page) and not is_template(page)

    @abstractmethod
    def process(self, pages: Iterable[Page]) -> Any:
        pass

    def execute_all(self) -> None:
        self.process(page for page in self.query_all() if self.filter(page))


class IterableAction(Action, metaclass=ABCMeta):
    def process(self, pages: Iterable[Page]):
        pages_it = peek(pages)
        if pages_it is None:
            return
        print(self)
        for page in pages_it:
            # TODO: check filter() before update
            #  process_page() may return Iterable[Callable[[], Any]] and defer execution to process()
            #  - like MediaScraper
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


def search_pages_by_last_edited_time(lower_bound: datetime, upper_bound: Optional[datetime] = None) -> list[Page]:
    # TODO: integrate with base function
    # Note: Notion APIs' last_edited_time info is only with minutes resolution
    lower_bound = lower_bound.replace(second=0, microsecond=0)
    pages = []
    for page in search_by_title('', 'page'):
        if upper_bound is not None and page.data.last_edited_time > upper_bound:
            continue
        if page.data.last_edited_time < lower_bound:
            break
        pages.append(page)
    logger.debug(pformat(pages, width=print_width))
    return pages


class Workflow:
    def __init__(self, actions: list[Action]):
        ...  # TODO

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime
from functools import wraps
from pprint import pformat
from typing import Iterable, Any, final, Optional

from loguru import logger

from notion_df.entity import Page, search_by_title
from notion_df.util.misc import repr_object
from notion_df.variable import print_width
from workflow.block_enum import exclude_template


class Action(metaclass=ABCMeta):
    def __repr__(self) -> str:
        return repr_object(self)

    def __init_subclass__(cls, **kwargs) -> None:
        process_pages_prev = cls.process_pages

        @wraps(process_pages_prev)
        def process_pages_new(self: Action, pages: Iterable[Page]):
            logger.info(self)
            return process_pages_prev(self, pages)

        setattr(cls, cls.process_pages.__name__, process_pages_new)

    @abstractmethod
    def process_all(self) -> Any:
        pass

    @abstractmethod
    def process_pages(self, pages: Iterable[Page]) -> Any:
        pass


class CompositeAction(Action):
    @abstractmethod
    def __init__(self, actions: list[Action]):
        self.actions = actions

    def process_all(self) -> Any:
        for action in self.actions:
            action.process_all()

    def process_pages(self, pages: Iterable[Page]) -> Any:
        for action in self.actions:
            action.process_pages(pages)


class IndividualAction(Action):
    def __repr__(self):
        return repr_object(self)

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        setattr(cls, cls.query.__name__, exclude_template(cls.query))

    @final
    def process_all(self) -> Any:
        return self.process_pages(self.query())

    @abstractmethod
    def query(self) -> Iterable[Page]:
        """full-scan mode"""
        pass

    @abstractmethod
    def process_pages(self, pages: Iterable[Page]) -> Any:
        pass


class SequentialAction(IndividualAction):
    @final
    def process_pages(self, pages: Iterable[Page]) -> Any:
        for page in pages:
            self.process_page(page)

    @abstractmethod
    def process_page(self, page: Page) -> Any:
        pass


@exclude_template
def search_pages_by_last_edited_time(lower_bound: datetime, upper_bound: Optional[datetime] = None) -> Iterable[Page]:
    """Note: Notion APIs' last_edited_time info is only with minutes resolution"""
    # TODO: integrate with base function
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

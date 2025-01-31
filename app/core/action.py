from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from pprint import pformat
from typing import Iterable, Any, final, Callable, TypeVar, Optional

from loguru import logger

from app.core.entrypoint import entrypoint, WorkflowRecord, WorkflowSkipException
from app.my_block import is_template
from notion_df.core.struct import repr_object
from notion_df.core.variable import print_width
from notion_df.entity import Page, Workspace

CallableT = TypeVar('CallableT', bound=Callable)


class Action(metaclass=ABCMeta):
    def __repr__(self) -> str:
        return repr_object(self)

    @abstractmethod
    def process_pages(self, pages: Iterable[Page]) -> Any:
        """process the given pages."""
        pass

    @abstractmethod
    def process_all(self) -> Any:
        """process with full-scan query."""
        pass

    @final
    def process_by_last_edited_time(self, lower_bound: datetime, upper_bound: Optional[datetime] = None) -> Any:
        """process with last-edited-time-based search query.
        Note: Notion APIs' last_edited_time info is only with minutes resolution"""
        logger.info(f"{self}.process_by_last_edited_time(): lower_bound - {lower_bound}, upper_bound - {upper_bound}")
        lower_bound = lower_bound.replace(second=0, microsecond=0)
        pages = set()
        for page in Workspace().search_by_title('', 'page', page_size=30):
            if upper_bound is not None and page.last_edited_time > upper_bound:
                continue
            if page.last_edited_time < lower_bound:
                break
            pages.add(page)
        logger.debug(f"Before filtered - {pformat(pages, width=print_width)}")
        pages.discard(Page(WorkflowRecord.page_id))
        pages = {page for page in pages if not is_template(page)}
        if not pages:
            raise WorkflowSkipException("No new record.")
        logger.debug(f"After filtered - {pformat(pages, width=print_width)}")
        return self.process_pages(pages)

    @entrypoint
    def run_by_last_edited_time(self, lower_bound: datetime, upper_bound: Optional[datetime] = None) -> Any:
        return self.process_by_last_edited_time(lower_bound, upper_bound)

    @entrypoint
    def run_all(self, update_last_success_time: bool = False) -> Any:
        with WorkflowRecord(update_last_success_time=update_last_success_time):
            return self.process_all()

    @entrypoint
    def run_recent(self, interval: timedelta, update_last_success_time: bool = False) -> Any:
        with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
            return self.process_by_last_edited_time(wf_rec.start_time - interval, wf_rec.start_time)

    @entrypoint
    def run_from_last_success(self, update_last_success_time: bool) -> Any:
        # TODO: if the last result was RetryError, sleep for 10 mins
        with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
            if wf_rec.last_success_time is None:
                self.process_all()
            return self.process_by_last_edited_time(wf_rec.last_success_time, None)


class CompositeAction(Action):
    def __init__(self, actions: list[Action]) -> None:
        self.actions = actions

    def process_all(self) -> Any:
        logger.info(f'#### {self}')
        for action in self.actions:
            action.process_all()

    def process_pages(self, pages: Iterable[Page]) -> Any:
        logger.info(f'#### {self}')
        for action in self.actions:
            action.process_pages(pages)


class IndividualAction(Action):
    @final
    def process_all(self) -> Any:
        logger.info(f'#### {self}')
        return self.process_pages(page for page in self.query() if not is_template(page))

    @abstractmethod
    def query(self) -> Iterable[Page]:
        pass


class SequentialAction(IndividualAction):
    @final
    def process_pages(self, pages: Iterable[Page]) -> Any:
        logger.info(f'#### {self}')
        for page in pages:
            self.process_page(page)

    @abstractmethod
    def process_page(self, page: Page) -> Any:
        pass

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Iterable, Any, final
from typing import Optional

from loguru import logger

from notion_df.entity import Page
from notion_df.util.misc import repr_object
from workflow.block_enum import is_template
from workflow.core.context import search_pages_by_last_edited_time, log_action, WorkflowRecord


class Action(metaclass=ABCMeta):
    def __repr__(self) -> str:
        return repr_object(self)

    @final
    def process_all(self) -> Any:
        """query and process"""
        logger.info(self)
        return self._process_all()

    @abstractmethod
    def _process_all(self) -> Any:
        pass

    @final
    def process_pages(self, pages: Iterable[Page]) -> Any:
        """process the given pages"""
        logger.info(self)
        return self._process_pages(pages)

    @abstractmethod
    def _process_pages(self, pages: Iterable[Page]) -> Any:
        pass

    def process_by_last_edited_time(self, lower_bound: datetime, upper_bound: Optional[datetime] = None) -> Any:
        recent_pages = search_pages_by_last_edited_time(lower_bound, upper_bound)
        return self.process_pages(recent_pages)

    @log_action
    def run_by_last_edited_time(self, lower_bound: datetime, upper_bound: Optional[datetime] = None) -> Any:
        return self.process_by_last_edited_time(lower_bound, upper_bound)

    @log_action
    def run_all(self, update_last_success_time: bool = False) -> Any:
        with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
            return self.process_all()

    @log_action
    def run_recent(self, interval: timedelta, update_last_success_time: bool = False) -> Any:
        with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
            return self.process_by_last_edited_time(wf_rec.start_time - interval, wf_rec.start_time)

    @log_action
    def run_from_last_success(self, update_last_success_time: bool) -> bool:
        # TODO: if the last result was RetryError, sleep for 10 mins
        with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
            if wf_rec.last_success_time is None:
                self.process_all()
            return self.process_by_last_edited_time(wf_rec.last_success_time, None)


class CompositeAction(Action):
    def __init__(self, actions: list[Action]):
        self.actions = actions

    def _process_all(self) -> Any:
        for action in self.actions:
            action._process_all()

    def _process_pages(self, pages: Iterable[Page]) -> Any:
        for action in self.actions:
            action._process_pages(pages)


class IndividualAction(Action):
    def __repr__(self):
        return repr_object(self)

    @final
    def _process_all(self) -> Any:
        return self._process_pages(page for page in self._query() if not is_template(page))

    @abstractmethod
    def _query(self) -> Iterable[Page]:
        pass

    @abstractmethod
    def _process_pages(self, pages: Iterable[Page]) -> Any:
        pass


class SequentialAction(IndividualAction):
    @final
    def _process_pages(self, pages: Iterable[Page]) -> Any:
        for page in pages:
            self._process_page(page)

    @abstractmethod
    def _process_page(self, page: Page) -> Any:
        pass

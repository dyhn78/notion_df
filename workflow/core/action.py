from __future__ import annotations

import json
import traceback
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from itertools import chain
from pprint import pformat
from typing import Iterable, Optional, cast, Any, Iterator, TypeVar, final
from uuid import UUID

import tenacity
from loguru import logger

from notion_df.core.serialization import deserialize_datetime
from notion_df.entity import Page, search_by_title, Block
from notion_df.object.data import DividerBlockValue, ParagraphBlockValue, ToggleBlockValue, CodeBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.util.misc import repr_object
from notion_df.variable import print_width, my_tz
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


# TODO: rewrite as Workflow.execute_by_...()
def execute_by_last_edited_time(actions: list[Action], lower_bound: datetime,
                                upper_bound: Optional[datetime] = None) -> bool:
    # TODO: if no recent_pages, raise SkipException instead of returning False
    recent_pages = set(search_pages_by_last_edited_time(lower_bound, upper_bound))
    recent_pages.discard(Page(log_page_id))
    if not recent_pages:
        return False
    for self in actions:
        self.process(page for page in recent_pages if self.filter(page))
    return True


def run_all(actions: list[Action]) -> None:
    with WorkflowLog(update_last_success_time=False):
        for action in actions:
            action.execute_all()


def run_from_last_edited_time_bound(actions: list[Action],
                                    timedelta_size: timedelta, update_last_success_time: bool) -> None:
    # TODO: if the last result was RetryError, sleep for 10 mins
    with WorkflowLog(update_last_success_time=update_last_success_time) as wf_log:
        execute_by_last_edited_time(actions, wf_log.start_time - timedelta_size, wf_log.start_time)


def run_from_last_success(actions: list[Action],
                          update_last_success_time: bool) -> bool:
    with WorkflowLog(update_last_success_time=update_last_success_time) as wf_log:
        if wf_log.last_success_time is not None:
            wf_log.enabled = execute_by_last_edited_time(actions, wf_log.last_success_time)
            return wf_log.enabled
        else:
            for action in actions:
                action.execute_all()
            return True


# TODO: do not update last_success_time if when the value has changed from the init
class WorkflowLog:
    # Note: the log_page is implemented as page with log blocks, not database with log pages,
    #  since Notion API does not directly support permanently deleting pages,
    #  and third party solutions like `https://github.com/pocc/bulk_delete_notion_pages`
    #  needs additional works to integrate.
    def __init__(self, *, update_last_success_time: bool):
        self.update_last_success_time = update_last_success_time
        self.start_time = datetime.now().astimezone(my_tz)
        self.start_time_str = self.start_time.strftime(log_date_format)
        self.start_time_group_str = self.start_time.strftime(log_date_group_format)
        self.enabled = True
        self.processed_pages: Optional[int] = None

        self.last_success_time_blocks = log_last_success_time_parent_block.retrieve_children()
        last_execution_time_block = self.last_success_time_blocks[0]
        self.last_execution_time_str = (cast(ParagraphBlockValue, last_execution_time_block.data.value)
                                        .rich_text.plain_text)
        if self.last_execution_time_str == 'STOP':
            logger.info("self.last_execution_time_str == 'STOP'")  # TODO refactor
            exit(0)
        if self.last_execution_time_str == 'ALL':
            self.last_success_time = None
        else:
            self.last_success_time = deserialize_datetime(self.last_execution_time_str)

    def __enter__(self) -> WorkflowLog:
        return self

    def format_time(self) -> str:
        execution_time = datetime.now().astimezone(my_tz) - self.start_time
        return f'{self.start_time_str} - {round(execution_time.total_seconds(), 3)} seconds'

    def __exit__(self, exc_type: type, exc_val, exc_tb) -> None:
        if not self.enabled:
            return
        child_block_values = []
        if exc_type is None:
            summary_text = f"success - {self.format_time()}"
            summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
            if self.update_last_success_time:
                log_last_success_time_parent_block.append_children([
                    ParagraphBlockValue(RichText([TextSpan(self.start_time_str)]))])
                for block in self.last_success_time_blocks:
                    block.delete()
        elif exc_type in [KeyboardInterrupt, json.JSONDecodeError, tenacity.RetryError]:
            summary_text = f"failure - {self.format_time()}: {exc_val}"
            summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
        else:
            # TODO: needs full print by redirecting print() stream to logger
            summary_text = f"error - {self.format_time()} - {exc_type.__name__} - {exc_val}"
            summary_block_value = ToggleBlockValue(RichText([TextSpan(summary_text), UserMention(my_user_id)]))
            traceback_str = traceback.format_exc()
            child_block_values = []
            for i in range(0, len(traceback_str), 1000):
                child_block_values.append(CodeBlockValue(RichText.from_plain_text(traceback_str[i:i + 1000])))

        log_group_block = None
        for block in reversed(log_page_block.retrieve_children()):
            if isinstance(block.data.value, DividerBlockValue):
                log_group_block = log_page_block.append_children([
                    ToggleBlockValue(RichText([TextSpan(self.start_time_group_str)]))])[0]
                break
            if cast(ToggleBlockValue, block.data.value).rich_text.plain_text == self.start_time_group_str:
                log_group_block = block
                break
            if self.start_time - block.data.created_time > timedelta(days=7):
                block.delete()
        assert isinstance(log_group_block, Block)

        summary_block = log_group_block.append_children([summary_block_value])[0]
        if child_block_values:
            summary_block.append_children(child_block_values)

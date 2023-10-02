from __future__ import annotations

import json
import traceback
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from itertools import chain
from pprint import pprint
from typing import Iterable, Optional, cast, Any
from uuid import UUID

from notion_df.core.serialization import deserialize_datetime
from notion_df.data.entity_data import DividerBlockValue, ParagraphBlockValue, ToggleBlockValue, CodeBlockValue
from notion_df.data.rich_text import RichText, TextSpan, UserMention
from notion_df.entity import Page, search_by_title, Block
from notion_df.util.misc import repr_object
from notion_df.variable import Settings, print_width, my_tz

my_user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')
log_page_id = '6d16dc6747394fca95dc169c8c736e2d'
log_page_block = Block(log_page_id)
log_date_format = '%Y-%m-%d %H:%M:%S+09:00'
log_date_group_format = '%Y-%m-%d'
log_last_success_time_parent_block = Block('c66d852e27e84d92b6203dfdadfefad8')


class Action(metaclass=ABCMeta):
    def __repr__(self):
        return repr_object(self)

    @abstractmethod
    def query_all(self) -> Iterable[Page]:
        pass

    @abstractmethod
    def filter(self, page: Page) -> bool:
        """from given retrieved pages, pick the ones which need to process.
        this is supposed to reflect the filter condition of query_all()."""
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]) -> Any:
        pass

    def execute_all(self) -> None:
        self.process(self.query_all())


class IterableAction(Action, metaclass=ABCMeta):
    def process(self, pages: Iterable[Page]):
        pages = iter(pages)
        try:
            _page = next(pages)
        except StopIteration:
            return
        print(self)
        for page in chain([_page], pages):
            self.process_page(page)

    @abstractmethod
    def process_page(self, page: Page):
        pass


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
    if Settings.print.enabled:
        pprint(pages, width=print_width)
    return pages


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


def run_all(actions: list[Action], print_body: bool) -> None:
    with Logger(print_body=print_body, update_last_success_time=False):
        for action in actions:
            action.execute_all()


def run_from_last_edited_time_bound(actions: list[Action], print_body: bool,
                                    timedelta_size: timedelta, update_last_success_time: bool) -> None:
    with Logger(print_body=print_body, update_last_success_time=update_last_success_time) as logger:
        execute_by_last_edited_time(actions, logger.start_time - timedelta_size, logger.start_time)


def run_from_last_success(actions: list[Action], print_body: bool,
                          update_last_success_time: bool) -> bool:
    with Logger(print_body=print_body, update_last_success_time=update_last_success_time) as logger:
        if logger.last_success_time is not None:
            logger.enabled = execute_by_last_edited_time(actions, logger.last_success_time)
            return logger.enabled
        else:
            for action in actions:
                action.execute_all()
            return True


class Logger:
    # Note: the log_page is implemented as page with log blocks, not database with log pages,
    #  since Notion API does not directly support permanently deleting pages,
    #  and third party solutions like `https://github.com/pocc/bulk_delete_notion_pages`
    #  needs additional works to integrate.
    def __init__(self, *, print_body: bool, update_last_success_time: bool):
        self.print_body = print_body
        self.update_last_success_time = update_last_success_time
        self.start_time = datetime.now().astimezone(my_tz)
        self.start_time_str = self.start_time.strftime(log_date_format)
        self.start_time_group_str = self.start_time.strftime(log_date_group_format)
        self.enabled = True
        self.processed_pages: Optional[int] = None

        self.last_success_time_blocks = log_last_success_time_parent_block.retrieve_children()
        last_execution_time_block = self.last_success_time_blocks[0]
        last_execution_time_str = cast(ParagraphBlockValue,
                                       last_execution_time_block.data.value).rich_text.plain_text
        if last_execution_time_str == 'ALL':
            self.last_success_time = None
        else:
            self.last_success_time = deserialize_datetime(last_execution_time_str)

    def __enter__(self) -> Logger:
        Settings.print.enabled = self.print_body
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

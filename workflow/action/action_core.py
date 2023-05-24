from __future__ import annotations

import traceback
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from functools import cached_property
from itertools import chain
from pprint import pprint
from typing import Iterable, Optional, cast
from uuid import UUID

from notion_df.entity import Page, search_by_title, Block
from notion_df.object.block import DividerBlockValue, ParagraphBlockValue, ToggleBlockValue, CodeBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.util.collection import Paginator
from notion_df.util.misc import repr_object
from notion_df.util.serialization import deserialize_datetime
from notion_df.variable import Settings, print_width, my_tz

min_timedelta: timedelta = timedelta(seconds=60)
my_user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')
log_page_id = '6d16dc6747394fca95dc169c8c736e2d'
log_page_block = Block(log_page_id)
log_date_format = '%Y-%m-%d %H:%M:%S+09:00'
log_date_group_format = '%Y-%m-%d'
log_last_success_time_block = Block('c66d852e27e84d92b6203dfdadfefad8')


class Action(metaclass=ABCMeta):
    def __repr__(self):
        return repr_object(self, [])

    @abstractmethod
    def query_all(self) -> Paginator[Page]:
        pass

    @abstractmethod
    def filter(self, page: Page) -> bool:
        """from given retrieved pages, pick the ones which need to process."""
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]):
        pass

    def execute_all(self):
        self.process(self.query_all())

    @classmethod
    def execute_by_last_edited_time(cls, actions: list[Action], lower_bound: datetime,
                                    upper_bound: Optional[datetime] = None) -> bool:
        # TODO: if no recent_pages, raise SkipException instead of returning False
        recent_pages = set(search_pages_by_last_edited_time(lower_bound, upper_bound))
        recent_pages.discard(Page(log_page_id))
        if not recent_pages:
            return False
        for self in actions:
            self.process(page for page in recent_pages if self.filter(page))
        return True


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
        if upper_bound is not None and page.last_edited_time > upper_bound:
            continue
        if page.last_edited_time < lower_bound:
            break
        pages.append(page)
    if Settings.print.enabled:
        pprint(pages, width=print_width)
    return pages


class Logger:
    # Note: the log_page is implemented as page with log blocks, not database with log pages,
    #  since Notion API does not directly support permanently deleting pages,
    #  and third party solutions like `https://github.com/pocc/bulk_delete_notion_pages`
    #  needs additional works to integrate.
    # TODO: add toggleable heading block for each day; extend the log storage to 7 days
    def __init__(self, *, print_body: bool):
        self.print_body = print_body
        self.start_time = datetime.now().astimezone(my_tz)
        self.start_time_str = self.start_time.strftime(log_date_format)
        self.start_time_group_str = self.start_time.strftime(log_date_group_format)
        self.enabled = True
        self.processed_pages: Optional[int] = None

        self.last_execution_time_blocks = log_last_success_time_block.retrieve_children()
        last_execution_time_block = self.last_execution_time_blocks[0]
        last_execution_time_str = cast(ParagraphBlockValue,
                                       last_execution_time_block.value).rich_text.plain_text
        if last_execution_time_str == 'ALL':
            self.last_success_time = None
        else:
            self.last_success_time = deserialize_datetime(last_execution_time_str)

    @cached_property
    def log_group_blocks(self):
        blocks = []
        for block in reversed(log_page_block.retrieve_children()):
            if isinstance(block.value, DividerBlockValue):
                break
            if self.start_time - block.created_time > timedelta(days=7):
                block.delete()
            blocks.append(block)
        return blocks

    def __enter__(self) -> Logger:
        Settings.print.enabled = self.print_body
        return self

    def format_time(self) -> str:
        execution_time = datetime.now().astimezone(my_tz) - self.start_time
        return f'{self.start_time_str} - {round(execution_time.total_seconds(), 3)} seconds'

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.enabled:
            return
        child_block_values = []
        if exc_type is None:
            summary_text = f"success - {self.format_time()}"
            summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
            for block in self.last_execution_time_blocks:
                block.delete()
            log_last_success_time_block.append_children([
                ParagraphBlockValue(RichText([TextSpan(self.start_time_str)]))])
        # elif exc_type == json.JSONDecodeError:
        #     summary_text = f"failure - {self.format_time()}: {exc_val}"
        #     summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
        else:
            summary_text = f"error - {self.format_time()} - {exc_type} - {exc_val}"
            summary_block_value = ToggleBlockValue(RichText([TextSpan(summary_text), UserMention(my_user_id)]))
            traceback_str = traceback.format_exc()
            child_block_values = []
            for i in range(0, len(traceback_str), 1000):
                child_block_values.append(CodeBlockValue(RichText.from_plain_text(traceback_str[i:i + 1000])))

        for group_block in self.log_group_blocks:
            if cast(ToggleBlockValue, group_block.value).rich_text.plain_text == self.start_time_group_str:
                break
        else:
            group_block = log_page_block.append_children([
                ToggleBlockValue(RichText([TextSpan(self.start_time_group_str)]))])[0]

        summary_block = group_block.append_children([summary_block_value])[0]
        if child_block_values:
            summary_block.append_children(child_block_values)

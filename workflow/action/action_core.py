from __future__ import annotations

import json
import traceback
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from pprint import pprint
from typing import Iterable, Optional
from uuid import UUID

from notion_df.entity import Page, Children, search_by_title, Block
from notion_df.object.block import DividerBlockValue, ParagraphBlockValue, ToggleBlockValue, CodeBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.util.serialization import deserialize_datetime
from notion_df.variable import Settings, print_width, my_tz

upper_bound_timedelta = timedelta(seconds=30)
my_user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')
log_page_id = '6d16dc6747394fca95dc169c8c736e2d'
log_page_block = Block(log_page_id)
log_date_format = '%Y-%m-%d %H:%M:%S+09:00'


class Action(metaclass=ABCMeta):
    @abstractmethod
    def query_all(self) -> Children[Page]:
        pass

    @abstractmethod
    def filter(self, record: Page) -> bool:
        """from given retrieved pages, pick the ones which need to process."""
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]):
        pass

    def execute_all(self):
        self.process(self.query_all())

    @classmethod
    def execute_by_last_edited_time(cls, actions: list[Action], lower_bound: datetime,
                                    upper_bound: Optional[datetime] = None):
        recent_pages = search_pages_by_last_edited_time(lower_bound, upper_bound)
        for self in actions:
            self.process(page for page in recent_pages if self.filter(page))


def search_pages_by_last_edited_time(lower_bound: datetime, upper_bound: Optional[datetime] = None) -> list[Page]:
    # TODO: integrate with base function
    # Note: Notion APIs' last_edited_time info is only with minutes resolution
    lower_bound = lower_bound.replace(second=0, microsecond=0)
    print(lower_bound.isoformat(), upper_bound.isoformat())
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
    def __init__(self, *, print_body: bool):
        self.print_body = print_body
        self.start_time = datetime.now().astimezone(my_tz)
        self.start_time_str = f"{self.start_time.strftime(log_date_format)}"

    def __enter__(self) -> Logger:
        Settings.print.enabled = self.print_body
        return self

    def format_time(self) -> str:
        execution_time = datetime.now().astimezone(my_tz) - self.start_time
        return f'{self.start_time_str} - {round(execution_time.total_seconds(), 3)} seconds'

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        child_block_values = []
        if exc_type is None:
            summary_text = f"success - {self.format_time()}"
            summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
        elif exc_type == json.JSONDecodeError:
            summary_text = f"failure - {self.format_time()}: {exc_val}"
            summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
        else:
            summary_text = f"error - {self.format_time()}: "
            summary_block_value = ToggleBlockValue(RichText([TextSpan(summary_text), UserMention(my_user_id)]))
            traceback_str = traceback.format_exc()
            child_block_values = []
            for i in range(0, len(traceback_str), 1000):
                child_block_values.append(CodeBlockValue(RichText.from_plain_text(traceback_str[i:i + 1000])))

        summary_block = log_page_block.append_children([summary_block_value])[0]
        if child_block_values:
            summary_block.append_children(child_block_values)

        prev_summary_blocks = log_page_block.retrieve_children()
        for block in prev_summary_blocks[3:]:
            if self.start_time - block.created_time > timedelta(days=1):
                block.delete()

    @staticmethod
    def get_last_success_time() -> Optional[datetime]:
        for block in reversed(log_page_block.retrieve_children()):
            if isinstance(block.value, DividerBlockValue):
                break
            try:
                # noinspection PyUnresolvedReferences
                last_execution_time_str = block.value.rich_text.plain_text
            except AttributeError:
                continue
            if last_execution_time_str.find('success') == -1:
                continue
            last_execution_time = deserialize_datetime(last_execution_time_str.split(' - ')[1])
            return last_execution_time

from __future__ import annotations

import inspect
import json
import traceback
from datetime import datetime, timedelta
from functools import wraps
from pprint import pformat
from typing import Optional, Iterable, Callable, ParamSpec, cast
from uuid import UUID

import tenacity
from loguru import logger

from notion_df.core.serialization import deserialize_datetime
from notion_df.entity import Page, search_by_title, Block
from notion_df.object.data import ParagraphBlockValue, ToggleBlockValue, CodeBlockValue, DividerBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.variable import print_width, my_tz
from workflow import log_dir
from workflow.block_enum import is_template


class WorkflowSkipException(Exception):
    pass


def search_pages_by_last_edited_time(lower_bound: datetime, upper_bound: Optional[datetime] = None) -> Iterable[Page]:
    """Note: Notion APIs' last_edited_time info is only with minutes resolution"""
    lower_bound = lower_bound.replace(second=0, microsecond=0)
    pages = set()
    for page in search_by_title('', 'page'):
        if upper_bound is not None and page.data.last_edited_time > upper_bound:
            continue
        if page.data.last_edited_time < lower_bound:
            break
        pages.add(page)
    logger.debug(pformat(pages, width=print_width))
    pages.discard(Page(WorkflowRecord.page_id))
    pages = {page for page in pages if not is_template(page)}
    if not pages:
        pass  # TODO: raise WorkflowSkipException if empty
    return pages


P = ParamSpec('P')


def log_action(func: Callable[P, bool]) -> Callable[P, bool]:
    # def get_latest_log_path() -> Optional[Path]:
    #     log_path_list = sorted(log_dir.iterdir())
    #     if not log_path_list:
    #         return None
    #     return log_path_list[-1]

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        logger.add(log_dir / '{time}.log',
                   # (get_latest_log_path() or (log_dir / '{time}.log')),
                   level='DEBUG', rotation='100 MB', retention=timedelta(weeks=2))
        logger.info(f'{"#" * 5} Start.')
        with logger.catch():  # TODO: recognize WorkflowSkipException (replace 'has_new_record')
            has_new_record = func(*args, **kwargs)
            logger.info(f'{"#" * 5} {"Done." if has_new_record else "No new record."}')
            return has_new_record

    wrapper.__signature__ = inspect.signature(func)
    return wrapper


class WorkflowRecord:
    user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')
    page_id = UUID('6d16dc6747394fca95dc169c8c736e2d')
    page_block = Block(page_id)
    last_success_time_parent_block = Block('c66d852e27e84d92b6203dfdadfefad8')
    date_format = '%Y-%m-%d %H:%M:%S+09:00'
    date_group_format = '%Y-%m-%d'

    # Note: the record page is implemented as page with log blocks, not database with log pages,
    #  since Notion API does not directly support permanently deleting pages,
    #  and third party solutions like `https://github.com/pocc/bulk_delete_notion_pages`
    #  needs additional works to integrate.
    def __init__(self, *, update_last_success_time: bool):
        self.update_last_success_time = update_last_success_time
        self.start_time = datetime.now().astimezone(my_tz)
        self.start_time_str = self.start_time.strftime(WorkflowRecord.date_format)
        self.start_time_group_str = self.start_time.strftime(WorkflowRecord.date_group_format)
        self.enabled = True
        self.processed_pages: Optional[int] = None

        self.last_success_time_blocks = WorkflowRecord.last_success_time_parent_block.retrieve_children()
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

    def __enter__(self) -> WorkflowRecord:
        return self

    def format_time(self) -> str:
        execution_time = datetime.now().astimezone(my_tz) - self.start_time
        return f'{self.start_time_str} - {round(execution_time.total_seconds(), 3)} seconds'

    def __exit__(self, exc_type: type, exc_val, exc_tb) -> None:
        if not self.enabled:  # TODO: recognize WorkflowSkipException (replace 'enabled')
            return
        child_block_values = []
        if exc_type is None:
            summary_text = f"success - {self.format_time()}"
            summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
            if self.update_last_success_time:
                WorkflowRecord.last_success_time_parent_block.append_children([
                    ParagraphBlockValue(RichText([TextSpan(self.start_time_str)]))])
                for block in self.last_success_time_blocks:
                    block.delete()
        elif exc_type in [KeyboardInterrupt, json.JSONDecodeError, tenacity.RetryError]:
            summary_text = f"failure - {self.format_time()}: {exc_val}"
            summary_block_value = ParagraphBlockValue(RichText([TextSpan(summary_text)]))
        else:
            # TODO: needs full print by redirecting print() stream to logger
            summary_text = f"error - {self.format_time()} - {exc_type.__name__} - {exc_val}"
            summary_block_value = ToggleBlockValue(
                RichText([TextSpan(summary_text), UserMention(WorkflowRecord.user_id)]))
            traceback_str = traceback.format_exc()
            child_block_values = []
            for i in range(0, len(traceback_str), 1000):
                child_block_values.append(CodeBlockValue(RichText.from_plain_text(traceback_str[i:i + 1000])))

        log_group_block = None
        for block in reversed(WorkflowRecord.page_block.retrieve_children()):
            if isinstance(block.data.value, DividerBlockValue):
                log_group_block = WorkflowRecord.page_block.append_children([
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

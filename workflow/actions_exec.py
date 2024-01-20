from __future__ import annotations

import inspect
import json
import traceback
from datetime import timedelta, datetime
from functools import wraps
from pathlib import Path
from typing import Optional, cast, Callable, ParamSpec
from uuid import UUID

import tenacity
from loguru import logger

from notion_df.core.serialization import deserialize_datetime
from notion_df.entity import Page, Block
from notion_df.object.data import ParagraphBlockValue, ToggleBlockValue, CodeBlockValue, DividerBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.variable import my_tz
from workflow import log_dir
from workflow.actions import get_actions
from workflow.core.action import Action, search_pages_by_last_edited_time


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
        if not self.enabled:
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


def get_latest_log_path() -> Optional[Path]:
    log_path_list = sorted(log_dir.iterdir())
    if not log_path_list:
        return
    return log_path_list[-1]


P = ParamSpec('P')


def log_actions(func: Callable[P, bool]) -> Callable[P, bool]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        logger.add(log_dir / '{time}.log',
                   # (get_latest_log_path() or (log_dir / '{time}.log')),
                   level='DEBUG', rotation='100 MB', retention=timedelta(weeks=2))
        logger.info(f'{"#" * 5} Start.')
        with logger.catch():
            has_new_record = func(*args, **kwargs)
            logger.info(f'{"#" * 5} {"Done." if has_new_record else "No new record."}')
            return has_new_record

    wrapper.__signature__ = inspect.signature(func)
    return wrapper


@log_actions
def execute_all(actions: list[Action]) -> bool:
    with WorkflowRecord(update_last_success_time=False):
        for action in actions:
            action.process_all()
    return True


@log_actions
def execute_by_last_edited_time(actions: list[Action], lower_bound: datetime,
                                upper_bound: Optional[datetime] = None) -> bool:
    # TODO: if no recent_pages, raise SkipException instead of returning False
    recent_pages = set(search_pages_by_last_edited_time(lower_bound, upper_bound))
    recent_pages.discard(Page(WorkflowRecord.page_id))
    recent_pages = {page for page in recent_pages}
    if not recent_pages:
        return False
    for action in actions:
        action.process_pages(page for page in recent_pages)
    return True


@log_actions
def execute_from_last_edited_time_bound(actions: list[Action],
                                        timedelta_size: timedelta, update_last_success_time: bool) -> bool:
    # TODO: if the last result was RetryError, sleep for 10 mins
    with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
        wf_rec.enabled = execute_by_last_edited_time(actions, wf_rec.start_time - timedelta_size, wf_rec.start_time)
        return wf_rec.enabled


@log_actions
def execute_from_last_success(actions: list[Action], update_last_success_time: bool) -> bool:
    with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
        if wf_rec.last_success_time is None:
            for action in actions:
                action.process_all()
            return True
        wf_rec.enabled = execute_by_last_edited_time(actions, wf_rec.last_success_time, None)
        return wf_rec.enabled


if __name__ == '__main__':
    execute_by_last_edited_time(get_actions(), datetime(2024, 1, 7, 17, 0, 0, tzinfo=my_tz), None)

from __future__ import annotations

import json
import traceback
from datetime import timedelta, datetime
from pathlib import Path
from typing import Optional, cast

import tenacity
from loguru import logger

from notion_df.core.serialization import deserialize_datetime
from notion_df.entity import Page, Block
from notion_df.object.data import ParagraphBlockValue, ToggleBlockValue, CodeBlockValue, DividerBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.variable import my_tz
from workflow import log_dir
from workflow.actions import get_actions
from workflow.core.action import Action, search_pages_by_last_edited_time, log_page_id, log_date_format, \
    log_date_group_format, log_last_success_time_parent_block, my_user_id, log_page_block


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


def execute_all(actions: list[Action]) -> None:
    with WorkflowLog(update_last_success_time=False):
        for action in actions:
            action.execute_all()


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


def execute_from_last_edited_time_bound(actions: list[Action],
                                        timedelta_size: timedelta, update_last_success_time: bool) -> None:
    # TODO: if the last result was RetryError, sleep for 10 mins
    with WorkflowLog(update_last_success_time=update_last_success_time) as wf_log:
        execute_by_last_edited_time(actions, wf_log.start_time - timedelta_size, wf_log.start_time)


def execute_from_last_success(actions: list[Action], update_last_success_time: bool) -> None:
    logger.add(log_dir / '{time}.log',
               # (get_latest_log_path() or (log_dir / '{time}.log')),
               level='DEBUG', rotation='100 MB', retention=timedelta(weeks=2))
    logger.info(f'{"#" * 5} Start.')
    with logger.catch():
        with WorkflowLog(update_last_success_time=update_last_success_time) as wf_log:
            if wf_log.last_success_time is not None:
                wf_log.enabled = execute_by_last_edited_time(actions, wf_log.last_success_time)
            else:
                for action in actions:
                    action.execute_all()
        logger.info(f'{"#" * 5} {"Done." if wf_log.enabled else "No new record."}')


def get_latest_log_path() -> Optional[Path]:
    log_path_list = sorted(log_dir.iterdir())
    if not log_path_list:
        return
    return log_path_list[-1]


if __name__ == '__main__':
    execute_from_last_success(actions=get_actions(), update_last_success_time=True)
    # execute_by_last_edited_time(get_actions(), datetime(2024, 1, 7, 17, 0, 0, tzinfo=my_tz), None)

from __future__ import annotations

from datetime import timedelta, datetime
from typing import Optional

from notion_df.variable import my_tz
from workflow.actions import get_actions
from workflow.core.action import Action
from workflow.core.context import search_pages_by_last_edited_time, log_action, WorkflowRecord


# TODO: integrate into Action
@log_action
def execute_all(actions: list[Action]) -> bool:
    with WorkflowRecord(update_last_success_time=False):
        for action in actions:
            action.process_all()
    return True


@log_action
def execute_by_last_edited_time(actions: list[Action], lower_bound: datetime,
                                upper_bound: Optional[datetime] = None) -> bool:
    # TODO: if no recent_pages, raise SkipException instead of returning False
    recent_pages = set(search_pages_by_last_edited_time(lower_bound, upper_bound))
    if not recent_pages:
        return False
    for action in actions:
        action.process_pages(page for page in recent_pages)
    return True


@log_action
def execute_from_last_edited_time_bound(actions: list[Action],
                                        timedelta_size: timedelta, update_last_success_time: bool) -> bool:
    # TODO: if the last result was RetryError, sleep for 10 mins
    with WorkflowRecord(update_last_success_time=update_last_success_time) as wf_rec:
        wf_rec.enabled = execute_by_last_edited_time(actions, wf_rec.start_time - timedelta_size, wf_rec.start_time)
        return wf_rec.enabled


@log_action
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

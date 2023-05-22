from __future__ import annotations

from datetime import timedelta

from workflow.action.action_core import Action, min_timedelta, Logger
from workflow.action.media_scraper import MediaScraper
from workflow.action.prop_matcher import MatchActionBase, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByRefDate, MatchReadingsStartDate
from workflow.constant.block_enum import DatabaseEnum


class Workflow:
    def __init__(self, create_window: bool):
        workspace = MatchActionBase()
        self.actions: list[Action] = [
            MatchWeekByDateValue(workspace),

            MatchDateByCreatedTime(workspace, DatabaseEnum.event_db, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.event_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.event_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.issue_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.issue_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.journal_db, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.journal_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.journal_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.note_db, '시작'),
            MatchWeekByRefDate(workspace, DatabaseEnum.note_db, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.topic_db, '시작'),
            MatchWeekByRefDate(workspace, DatabaseEnum.topic_db, '시작', '시작'),

            MatchReadingsStartDate(workspace),
            MatchDateByCreatedTime(workspace, DatabaseEnum.reading_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.reading_db, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.section_db, '시작'),
            MatchWeekByRefDate(workspace, DatabaseEnum.section_db, '시작', '시작'),

            # TODO 배포후: <마디 - 🟢시작, 💚시작> 제거
            # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)

            MediaScraper(create_window),
        ]


def run_all(print_body: bool, create_window: bool) -> None:
    with Logger(print_body=print_body):
        workflow = Workflow(create_window)
        for action in workflow.actions:
            action.execute_all()


def run_from_last_edited_time_bound(print_body: bool, create_window: bool, window: timedelta) -> None:
    with Logger(print_body=print_body) as logger:
        workflow = Workflow(create_window)
        Action.execute_by_last_edited_time(workflow.actions, logger.start_time - window, logger.start_time)


def run_from_last_success(print_body: bool, create_window: bool) -> bool:
    with Logger(print_body=print_body) as logger:
        workflow = Workflow(create_window)
        last_success_time = logger.get_last_success_time()
        if last_success_time is not None:
            lower_bound = (last_success_time - min_timedelta
                           - timedelta(minutes=1))  # just in case
            upper_bound = logger.start_time - min_timedelta
            log_enabled = Action.execute_by_last_edited_time(workflow.actions, lower_bound, upper_bound)
            logger.enabled = log_enabled
            return log_enabled
        else:
            for action in workflow.actions:
                action.execute_all()
            return True


if __name__ == '__main__':
    run_from_last_success(print_body=True, create_window=False)

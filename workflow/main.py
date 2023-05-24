from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from workflow import project_root
from workflow.action.action_core import Action, min_timedelta, Logger
from workflow.action.media_scraper import MediaScraper
from workflow.action.migration_backup import MigrationBackupSaveAction
from workflow.action.prop_matcher import MatchActionBase, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByRefDate, MatchReadingsStartDate
from workflow.constant.block_enum import DatabaseEnum


class Workflow:
    def __init__(self, create_window: bool, backup_path: Path):
        base = MatchActionBase()
        self.actions: list[Action] = [
            MatchWeekByDateValue(base),

            MatchDateByCreatedTime(base, DatabaseEnum.event_db, '일간'),
            MatchDateByCreatedTime(base, DatabaseEnum.event_db, '생성'),
            MatchWeekByRefDate(base, DatabaseEnum.event_db, '주간', '일간'),

            MatchDateByCreatedTime(base, DatabaseEnum.issue_db, '생성'),
            MatchWeekByRefDate(base, DatabaseEnum.issue_db, '주간', '일간'),

            MatchDateByCreatedTime(base, DatabaseEnum.journal_db, '일간'),
            MatchDateByCreatedTime(base, DatabaseEnum.journal_db, '생성'),
            MatchWeekByRefDate(base, DatabaseEnum.journal_db, '주간', '일간'),

            MatchDateByCreatedTime(base, DatabaseEnum.note_db, '시작'),
            MatchWeekByRefDate(base, DatabaseEnum.note_db, '시작', '시작'),

            MatchDateByCreatedTime(base, DatabaseEnum.topic_db, '시작'),
            MatchWeekByRefDate(base, DatabaseEnum.topic_db, '시작', '시작'),

            MatchReadingsStartDate(base),
            MatchDateByCreatedTime(base, DatabaseEnum.reading_db, '생성'),
            MatchWeekByRefDate(base, DatabaseEnum.reading_db, '시작', '시작'),

            MatchDateByCreatedTime(base, DatabaseEnum.section_db, '시작'),
            MatchWeekByRefDate(base, DatabaseEnum.section_db, '시작', '시작'),

            # TODO 배포후: <마디 - 🟢시작, 💚시작> 제거
            # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)

            MediaScraper(create_window),

            MigrationBackupSaveAction(backup_path),
        ]


def run_all(print_body: bool, create_window: bool, backup_path: Path) -> None:
    with Logger(print_body=print_body):
        workflow = Workflow(create_window, backup_path)
        for action in workflow.actions:
            action.execute_all()


def run_from_last_edited_time_bound(print_body: bool, create_window: bool, backup_path: Path,
                                    timedelta_size: timedelta) -> None:
    with Logger(print_body=print_body) as logger:
        workflow = Workflow(create_window, backup_path)
        Action.execute_by_last_edited_time(workflow.actions, logger.start_time - timedelta_size, logger.start_time)


def run_from_last_success(print_body: bool, create_window: bool, backup_path: Path) -> bool:
    with Logger(print_body=print_body) as logger:
        workflow = Workflow(create_window, backup_path)
        if logger.last_success_time is not None:
            lower_bound = logger.last_success_time - min_timedelta
            upper_bound = logger.start_time - min_timedelta
            logger.enabled = Action.execute_by_last_edited_time(workflow.actions, lower_bound, upper_bound)
            return logger.enabled
        else:
            for action in workflow.actions:
                action.execute_all()
            return True


if __name__ == '__main__':
    run_from_last_success(print_body=True, create_window=False, backup_path=project_root / 'backup')
    # run_from_last_edited_time_bound(print_body=True, create_window=False, timedelta_size=timedelta(minutes=3))

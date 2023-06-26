from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from workflow import project_path
from workflow.action.action_core import Action, Logger
from workflow.action.media_scraper import MediaScraper
from workflow.action.migration_backup import MigrationBackupSaveAction, MigrationBackupLoadAction
from workflow.action.prop_matcher import MatchActionBase, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByRefDate, MatchReadingsStartDate, MatchStream
from workflow.constant.block_enum import DatabaseEnum

default_backup_path = project_path / 'backup'


# TODO: move to actions/main.py
def get_actions(create_window: bool, backup_path: Path) -> list[Action]:
    base = MatchActionBase()
    return [
        MigrationBackupLoadAction(backup_path),
        MigrationBackupSaveAction(backup_path),

        MatchWeekByDateValue(base),

        MatchDateByCreatedTime(base, DatabaseEnum.event_db, '일간'),
        MatchDateByCreatedTime(base, DatabaseEnum.event_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.event_db, '주간', '일간'),
        MatchStream(base, DatabaseEnum.event_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
                    DatabaseEnum.stream_db.prefix_title, DatabaseEnum.stream_db.prefix + '진행'),
        MatchStream(base, DatabaseEnum.event_db, DatabaseEnum.reading_db, DatabaseEnum.reading_db.prefix_title,
                    DatabaseEnum.stream_db.prefix_title, DatabaseEnum.stream_db.prefix + '진행'),

        MatchDateByCreatedTime(base, DatabaseEnum.issue_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.issue_db, '주간', '일간'),

        MatchDateByCreatedTime(base, DatabaseEnum.journal_db, '일간'),
        MatchDateByCreatedTime(base, DatabaseEnum.journal_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.journal_db, '주간', '일간'),

        MatchDateByCreatedTime(base, DatabaseEnum.stage_db, '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.stage_db, '주간', '일간'),

        MatchReadingsStartDate(base),
        MatchDateByCreatedTime(base, DatabaseEnum.reading_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.reading_db, '시작', '시작'),

        MatchDateByCreatedTime(base, DatabaseEnum.point_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.point_db, '생성', '생성'),

        MatchDateByCreatedTime(base, DatabaseEnum.topic_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.topic_db, '생성', '생성'),

        # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)

        MediaScraper(create_window),
    ]


def run_all(print_body: bool, create_window: bool, backup_path: Path) -> None:
    with Logger(print_body=print_body, update_last_success_time=False):
        for action in get_actions(create_window, backup_path):
            action.execute_all()


def run_from_last_edited_time_bound(print_body: bool, create_window: bool, backup_path: Path,
                                    timedelta_size: timedelta, update_last_success_time: bool) -> None:
    with Logger(print_body=print_body, update_last_success_time=update_last_success_time) as logger:
        Action.execute_by_last_edited_time(get_actions(create_window, backup_path),
                                           logger.start_time - timedelta_size, logger.start_time)


def run_from_last_success(print_body: bool, create_window: bool, backup_path: Path,
                          update_last_success_time: bool) -> bool:
    with Logger(print_body=print_body, update_last_success_time=update_last_success_time) as logger:
        actions = get_actions(create_window, backup_path)
        if logger.last_success_time is not None:
            logger.enabled = Action.execute_by_last_edited_time(
                actions, logger.last_success_time)
            return logger.enabled
        else:
            for action in actions:
                action.execute_all()
            return True


if __name__ == '__main__':
    pass
    run_from_last_success(print_body=True, create_window=False, backup_path=default_backup_path,
                          update_last_success_time=False)
    # run_from_last_success(print_body=True, create_window=False, backup_path=backup_path)
    # run_from_last_edited_time_bound(print_body=True, create_window=False, timedelta_size=timedelta(hours=3),
    #                                 backup_path=backup_path, update_last_success_time=False)

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Optional

from loguru import logger

from workflow import backup_dir, log_dir
from workflow.action.media_scraper import MediaScraper
from workflow.action.migration_backup import MigrationBackupSaveAction, MigrationBackupLoadAction
from workflow.action.prop_matcher import MatchActionBase, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByRefDate, MatchReadingsStartDate, MatchTopic, MatchTimeManualValue
from workflow.block_enum import DatabaseEnum
from workflow.core.action import Action
from workflow.core.action import run_from_last_success


def get_actions() -> list[Action]:
    base = MatchActionBase()
    return [
        MigrationBackupLoadAction(backup_dir),
        MigrationBackupSaveAction(backup_dir),

        MatchWeekByDateValue(base),

        MatchDateByCreatedTime(base, DatabaseEnum.journal_db, '일간'),
        MatchDateByCreatedTime(base, DatabaseEnum.journal_db, '정리'),
        MatchWeekByRefDate(base, DatabaseEnum.journal_db, '주간', '일간'),
        MatchTimeManualValue(base, DatabaseEnum.journal_db, '일간'),
        MatchTopic(base, DatabaseEnum.journal_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
                   DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        # MatchTopic(base, DatabaseEnum.journal_db, DatabaseEnum.stage_db, DatabaseEnum.stage_db.prefix_title,
        #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        MatchTopic(base, DatabaseEnum.journal_db, DatabaseEnum.reading_db, DatabaseEnum.reading_db.prefix_title,
                   DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        MatchDateByCreatedTime(base, DatabaseEnum.stage_db, '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.stage_db, '주간', '일간'),

        MatchDateByCreatedTime(base, DatabaseEnum.issue_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.issue_db, '주간', '일간'),
        MatchReadingsStartDate(base),
        MatchDateByCreatedTime(base, DatabaseEnum.reading_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.reading_db, '주간', '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.reading_db, '시작', '시작'),  # TODO: can be deprecated

        MatchWeekByRefDate(base, DatabaseEnum.topic_db, '주간', '일간'),
        MatchDateByCreatedTime(base, DatabaseEnum.point_db, '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.point_db, '주간', '일간'),

        MatchDateByCreatedTime(base, DatabaseEnum.schedule_db, '정리'),
        MatchWeekByRefDate(base, DatabaseEnum.schedule_db, '주간', '일간'),
        MatchTopic(base, DatabaseEnum.schedule_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
                   DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        MatchTopic(base, DatabaseEnum.schedule_db, DatabaseEnum.reading_db, DatabaseEnum.reading_db.prefix_title,
                   DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        MatchDateByCreatedTime(base, DatabaseEnum.review_db, '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.review_db, '주간', '일간'),

        # MatchDateByCreatedTime(base, DatabaseEnum.depr_journal_db, '일간'),
        # MatchDateByCreatedTime(base, DatabaseEnum.depr_journal_db, '생성'),
        # MatchWeekByRefDate(base, DatabaseEnum.depr_journal_db, '주간', '일간'),
        # MatchTimeManualValue(base, DatabaseEnum.depr_journal_db, '일간'),
        #
        # MatchDateByCreatedTime(base, DatabaseEnum.depr_subject_db, '일간'),
        # MatchWeekByRefDate(base, DatabaseEnum.depr_subject_db, '주간', '일간'),

        MediaScraper(create_window=False),
    ]


def get_latest_log_path() -> Optional[Path]:
    log_path_list = sorted(log_dir.iterdir())
    if not log_path_list:
        return
    return log_path_list[-1]


if __name__ == '__main__':
    logger.add((get_latest_log_path() or (log_dir / '{time}.log')),
               level='DEBUG', rotation='100 MB', retention=timedelta(weeks=2))
    logger.info(f'{"#" * 5} Start.')
    new_record = run_from_last_success(actions=get_actions(), update_last_success_time=True)
    logger.info(f'{"#" * 5} {"Done." if new_record else "No new record."}')

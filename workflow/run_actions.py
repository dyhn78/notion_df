from __future__ import annotations

from pathlib import Path

from workflow import backup_path
from workflow.core.action import Action
from workflow.action.media_scraper import MediaScraper
from workflow.action.migration_backup import MigrationBackupSaveAction, MigrationBackupLoadAction
from workflow.action.prop_matcher import MatchActionBase, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByRefDate, MatchReadingsStartDate, MatchTopic, MatchTimeManualValue
from workflow.block_enum import DatabaseEnum


def get_actions(create_window: bool, _backup_path: Path) -> list[Action]:
    base = MatchActionBase()
    return [
        MigrationBackupLoadAction(_backup_path),
        MigrationBackupSaveAction(_backup_path),

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

        MediaScraper(create_window),
    ]


actions = get_actions(False, backup_path)

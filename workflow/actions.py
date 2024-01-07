from __future__ import annotations

from workflow import backup_dir
from workflow.action.media_scraper import MediaScraper
from workflow.action.migration_backup import MigrationBackupLoadAction, MigrationBackupSaveAction
from workflow.action.prop_matcher import MatchActionBase, MatchWeekByDateValue, MatchEventProgress, \
    MatchDateByCreatedTime, MatchWeekByRefDate, MatchTimeManualValue, MatchReadingsStartDate
from workflow.block_enum import DatabaseEnum
from workflow.core.action import Action


def get_actions() -> list[Action]:
    base = MatchActionBase()
    return [
        MigrationBackupLoadAction(backup_dir),
        MigrationBackupSaveAction(backup_dir),

        MatchWeekByDateValue(base),

        MatchEventProgress(base),

        MatchDateByCreatedTime(base, DatabaseEnum.event_db, '일간', read_title=True, write_title=True),
        MatchDateByCreatedTime(base, DatabaseEnum.event_db, '정리'),
        MatchWeekByRefDate(base, DatabaseEnum.event_db, '주간', '일간'),
        MatchTimeManualValue(base, DatabaseEnum.event_db, '일간'),
        MatchDateByCreatedTime(base, DatabaseEnum.journal_db, '일간', read_title=True, write_title=True),
        MatchWeekByRefDate(base, DatabaseEnum.journal_db, '주간', '일간'),

        MatchDateByCreatedTime(base, DatabaseEnum.issue_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.issue_db, '주간', '일간'),
        MatchReadingsStartDate(base),
        MatchDateByCreatedTime(base, DatabaseEnum.reading_db, '생성'),
        MatchWeekByRefDate(base, DatabaseEnum.reading_db, '주간', '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.reading_db, '시작', '시작'),  # TODO: can be deprecated

        MatchWeekByRefDate(base, DatabaseEnum.topic_db, '주간', '일간'),
        MatchDateByCreatedTime(base, DatabaseEnum.point_db, '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.point_db, '주간', '일간'),

        MatchDateByCreatedTime(base, DatabaseEnum.depr_schedule_db, '정리'),
        MatchWeekByRefDate(base, DatabaseEnum.depr_schedule_db, '주간', '일간'),
        MatchDateByCreatedTime(base, DatabaseEnum.depr_review_db, '일간'),
        MatchWeekByRefDate(base, DatabaseEnum.depr_review_db, '주간', '일간'),

        MediaScraper(create_window=False),

        # DeprMatchTopic(base, DatabaseEnum.event_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
        #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        # DeprMatchTopic(base, DatabaseEnum.event_db, DatabaseEnum.event_db, DatabaseEnum.event_db.prefix_title,
        #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        # DeprMatchTopic(base, DatabaseEnum.event_db, DatabaseEnum.reading_db, DatabaseEnum.reading_db.prefix_title,
        #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        # DeprMatchTopic(base, DatabaseEnum.depr_schedule_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
        #                DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        # DeprMatchTopic(base, DatabaseEnum.depr_schedule_db, DatabaseEnum.reading_db,
        #                DatabaseEnum.reading_db.prefix_title,
        #                DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
        # MatchDateByCreatedTime(base, DatabaseEnum.depr_event_db, '일간'),
        # MatchDateByCreatedTime(base, DatabaseEnum.depr_event_db, '생성'),
        # MatchWeekByRefDate(base, DatabaseEnum.depr_event_db, '주간', '일간'),
        # MatchTimeManualValue(base, DatabaseEnum.depr_event_db, '일간'),
        # MatchDateByCreatedTime(base, DatabaseEnum.depr_subject_db, '일간'),
        # MatchWeekByRefDate(base, DatabaseEnum.depr_subject_db, '주간', '일간'),
    ]

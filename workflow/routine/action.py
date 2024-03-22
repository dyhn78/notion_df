from __future__ import annotations

from workflow import backup_dir
from workflow.action.media_scraper import MediaScraper
from workflow.action.migration_backup import MigrationBackupLoadAction, MigrationBackupSaveAction
from workflow.action.prop_matcher import MatchActionBase, MatchWeekiByDateValue, MatchDatei, \
    MatchWeekiByRefDate, MatchTimestr, MatchReadingDatei, MatchEventProgress, CreateProgressEvent
from workflow.block_enum import DatabaseEnum
from workflow.core.action import CompositeAction

base = MatchActionBase()
action = CompositeAction([
    MigrationBackupLoadAction(backup_dir),
    MigrationBackupSaveAction(backup_dir),

    MatchWeekiByDateValue(base),

    MatchDatei(base, DatabaseEnum.event_db, '일간', read_title=True, write_title=True),
    MatchDatei(base, DatabaseEnum.event_db, '정리'),
    MatchWeekiByRefDate(base, DatabaseEnum.event_db, '주간', '일간'),
    MatchTimestr(base, DatabaseEnum.event_db, '일간'),
    MatchEventProgress(base, DatabaseEnum.issue_db),
    MatchEventProgress(base, DatabaseEnum.reading_db),

    MatchDatei(base, DatabaseEnum.journal_db, '정리'),
    MatchWeekiByRefDate(base, DatabaseEnum.journal_db, '주간', '일간'),

    MatchDatei(base, DatabaseEnum.stage_db, '일간', read_title=True, write_title=True),
    MatchWeekiByRefDate(base, DatabaseEnum.stage_db, '주간', '일간'),

    MatchDatei(base, DatabaseEnum.point_db, '일간'),
    MatchWeekiByRefDate(base, DatabaseEnum.point_db, '주간', '일간'),

    MatchDatei(base, DatabaseEnum.issue_db, '생성'),
    MatchWeekiByRefDate(base, DatabaseEnum.issue_db, '주간', '일간'),
    CreateProgressEvent(base, DatabaseEnum.issue_db),

    MatchReadingDatei(base),
    MatchDatei(base, DatabaseEnum.reading_db, '생성'),
    MatchWeekiByRefDate(base, DatabaseEnum.reading_db, '주간', '일간'),
    MatchWeekiByRefDate(base, DatabaseEnum.reading_db, '시작', '시작'),  # TODO: can be deprecated
    CreateProgressEvent(base, DatabaseEnum.reading_db),

    MatchWeekiByRefDate(base, DatabaseEnum.topic_db, '주간', '일간'),

    MatchDatei(base, DatabaseEnum.gist_db, '일간'),
    MatchWeekiByRefDate(base, DatabaseEnum.gist_db, '주간', '일간'),

    MediaScraper(create_window=False),

    # DeprMatchTopic(base, DatabaseEnum.event_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
    #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchTopic(base, DatabaseEnum.event_db, DatabaseEnum.event_db, DatabaseEnum.event_db.prefix_title,
    #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchTopic(base, DatabaseEnum.event_db, DatabaseEnum.reading_db, DatabaseEnum.reading_db.prefix_title,
    #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchTopic(base, DatabaseEnum.journal_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
    #                DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchTopic(base, DatabaseEnum.journal_db, DatabaseEnum.reading_db,
    #                DatabaseEnum.reading_db.prefix_title,
    #                DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # MatchDatei(base, DatabaseEnum.depr_event_db, '일간'),
    # MatchDatei(base, DatabaseEnum.depr_event_db, '생성'),
    # MatchWeekiByRefDate(base, DatabaseEnum.depr_event_db, '주간', '일간'),
    # MatchTimestr(base, DatabaseEnum.depr_event_db, '일간'),
    # MatchDatei(base, DatabaseEnum.depr_subject_db, '일간'),
    # MatchWeekiByRefDate(base, DatabaseEnum.depr_subject_db, '주간', '일간'),
])

if __name__ == '__main__':
    from datetime import timedelta

    action.run_recent(interval=timedelta(hours=1))
    # action.run_by_last_edited_time(datetime(2024, 1, 7, 17, 0, 0, tzinfo=my_tz), None)
    # action.run_from_last_success(update_last_success_time=True)
    pass

from __future__ import annotations

from workflow import backup_dir
from workflow.action.match import MatchActionBase, MatchDatei, MatchRecordDatei, \
    MatchRecordWeekiByDatei, MatchRecordTimestr, MatchReadingStartDatei, MatchEventProgress
from workflow.action.media_scrap import MediaScrapAction
from workflow.action.migration_backup import MigrationBackupLoadAction, MigrationBackupSaveAction
from workflow.block_enum import DatabaseEnum
from workflow.core.action import CompositeAction

base = MatchActionBase()
routine_action = CompositeAction([
    MigrationBackupLoadAction(backup_dir),
    MigrationBackupSaveAction(backup_dir),

    MatchDatei(base),

    MatchRecordDatei(base, DatabaseEnum.event_db, '일간'),
    MatchRecordDatei(base, DatabaseEnum.event_db, '일정', read_title=True, write_title='always'),
    MatchRecordWeekiByDatei(base, DatabaseEnum.event_db, '일정', '일정'),
    MatchRecordTimestr(base, DatabaseEnum.event_db, '일정'),
    MatchEventProgress(base, DatabaseEnum.issue_db),
    MatchEventProgress(base, DatabaseEnum.reading_db),

    MatchRecordDatei(base, DatabaseEnum.journal_db, '일간'),
    MatchRecordDatei(base, DatabaseEnum.journal_db, '일정', read_title=True, write_title='if_separator_exists'),
    MatchRecordWeekiByDatei(base, DatabaseEnum.journal_db, '일정', '일정'),

    MatchRecordDatei(base, DatabaseEnum.thread_db, '일간', read_title=True, write_title='always'),
    MatchRecordWeekiByDatei(base, DatabaseEnum.thread_db, '주간', '일간'),

    MatchRecordDatei(base, DatabaseEnum.idea_db, '일간'),
    MatchRecordWeekiByDatei(base, DatabaseEnum.idea_db, '주간', '일간'),

    MatchRecordDatei(base, DatabaseEnum.issue_db, '일간'),  # Note: `read_title=False` set purposely here
    MatchRecordWeekiByDatei(base, DatabaseEnum.issue_db, '일정', '일정'),
    # DeprCreateDateEvent(base, DatabaseEnum.issue_db),

    MatchRecordDatei(base, DatabaseEnum.reading_db, '일간'),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, '주간', '일간'),
    MatchReadingStartDatei(base),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, '시작', '시작'),
    # DeprCreateDateEvent(base, DatabaseEnum.reading_db),

    MatchRecordDatei(base, DatabaseEnum.summit_db, '일간'),
    MatchRecordWeekiByDatei(base, DatabaseEnum.summit_db, '주간', '일간'),

    MatchRecordDatei(base, DatabaseEnum.gist_db, '일간'),
    MatchRecordWeekiByDatei(base, DatabaseEnum.gist_db, '주간', '일간'),

    MediaScrapAction(create_window=False),

    # DeprMatchRecordTopic(base, DatabaseEnum.event_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
    #            DatabaseEnum.summit_db.prefix_title, DatabaseEnum.summit_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.event_db, DatabaseEnum.event_db, DatabaseEnum.event_db.prefix_title,
    #            DatabaseEnum.summit_db.prefix_title, DatabaseEnum.summit_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.event_db, DatabaseEnum.reading_db, DatabaseEnum.reading_db.prefix_title,
    #            DatabaseEnum.summit_db.prefix_title, DatabaseEnum.summit_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.journal_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
    #                DatabaseEnum.summit_db.prefix_title, DatabaseEnum.summit_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.journal_db, DatabaseEnum.reading_db,
    #                DatabaseEnum.reading_db.prefix_title,
    #                DatabaseEnum.summit_db.prefix_title, DatabaseEnum.summit_db.prefix_title),
    # MatchRecordDatei(base, DatabaseEnum.depr_event_db, '일간'),
    # MatchRecordDatei(base, DatabaseEnum.depr_event_db, '생성'),
    # MatchRecordWeekiByDatei(base, DatabaseEnum.depr_event_db, '주간', '일간'),
    # MatchRecordTimestr(base, DatabaseEnum.depr_event_db, '일간'),
    # MatchRecordDatei(base, DatabaseEnum.depr_subject_db, '일간'),
    # MatchRecordWeekiByDatei(base, DatabaseEnum.depr_subject_db, '주간', '일간'),
])

if __name__ == '__main__':
    from datetime import timedelta

    routine_action.run_recent(interval=timedelta(minutes=120))
    # routine_action.run_by_last_edited_time(datetime(2024, 1, 7, 17, 0, 0, tzinfo=my_tz), None)
    # routine_action.run_from_last_success(update_last_success_time=True)
    pass

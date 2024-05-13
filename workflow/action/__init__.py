from __future__ import annotations

from workflow import backup_dir
from workflow.action.match import MatchActionBase, MatchDatei, MatchRecordDatei, \
    MatchRecordWeekiByDatei, MatchRecordTimestr, MatchReadingStartDatei, MatchEventProgress, MatchRecordDateiSchedule
from workflow.action.media_scrap import MediaScrapAction
from workflow.action.migration_backup import MigrationBackupLoadAction, MigrationBackupSaveAction
from workflow.block_enum import DatabaseEnum, schedule, start
from workflow.core.action import CompositeAction

base = MatchActionBase()
routine_action = CompositeAction([
    MigrationBackupLoadAction(backup_dir),
    MigrationBackupSaveAction(backup_dir),

    MatchDatei(base),

    MatchRecordDatei(base, DatabaseEnum.event_db, DatabaseEnum.datei_db.title),
    MatchRecordDatei(base, DatabaseEnum.event_db, schedule, read_datei_from_title=True, prepend_datei_on_title=True),
    MatchRecordDateiSchedule(base, DatabaseEnum.event_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.event_db, schedule, schedule),
    MatchRecordTimestr(base, DatabaseEnum.event_db, schedule),
    MatchEventProgress(base, DatabaseEnum.issue_db),
    MatchEventProgress(base, DatabaseEnum.reading_db),

    MatchRecordDatei(base, DatabaseEnum.journal_db, DatabaseEnum.datei_db.title),
    MatchRecordDatei(base, DatabaseEnum.journal_db, schedule, read_datei_from_title=True, prepend_datei_on_title=True,
                     is_journal=True),
    MatchRecordDateiSchedule(base, DatabaseEnum.journal_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.journal_db, schedule, schedule),

    MatchRecordDatei(base, DatabaseEnum.thread_db, DatabaseEnum.datei_db.title, read_datei_from_title=True,
                     prepend_datei_on_title=True),
    MatchRecordWeekiByDatei(base, DatabaseEnum.thread_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDatei(base, DatabaseEnum.idea_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.idea_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDatei(base, DatabaseEnum.issue_db, DatabaseEnum.datei_db.title),
    MatchRecordDatei(base, DatabaseEnum.issue_db, schedule, read_datei_from_created_time=False, read_datei_from_title=True),
    MatchRecordDateiSchedule(base, DatabaseEnum.issue_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.issue_db, schedule, schedule),
    # DeprCreateDateEvent(base, DatabaseEnum.issue_db),

    MatchRecordDatei(base, DatabaseEnum.reading_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),
    MatchReadingStartDatei(base),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, start, start),
    # DeprCreateDateEvent(base, DatabaseEnum.reading_db),

    MatchRecordDatei(base, DatabaseEnum.topic_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.topic_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDatei(base, DatabaseEnum.gist_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.gist_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MediaScrapAction(create_window=False),

    # DeprMatchRecordTopic(base, DatabaseEnum.event_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
    #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.event_db, DatabaseEnum.event_db, DatabaseEnum.event_db.prefix_title,
    #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.event_db, DatabaseEnum.reading_db, DatabaseEnum.reading_db.prefix_title,
    #            DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.journal_db, DatabaseEnum.issue_db, DatabaseEnum.issue_db.prefix_title,
    #                DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # DeprMatchRecordTopic(base, DatabaseEnum.journal_db, DatabaseEnum.reading_db,
    #                DatabaseEnum.reading_db.prefix_title,
    #                DatabaseEnum.topic_db.prefix_title, DatabaseEnum.topic_db.prefix_title),
    # MatchRecordDatei(base, DatabaseEnum.depr_event_db, '일간'),
    # MatchRecordDatei(base, DatabaseEnum.depr_event_db, '생성'),
    # MatchRecordWeekiByDatei(base, DatabaseEnum.depr_event_db, '주간', '일간'),
    # MatchRecordTimestr(base, DatabaseEnum.depr_event_db, '일간'),
    # MatchRecordDatei(base, DatabaseEnum.depr_subject_db, '일간'),
    # MatchRecordWeekiByDatei(base, DatabaseEnum.depr_subject_db, '주간', '일간'),
])

if __name__ == '__main__':
    from datetime import timedelta

    routine_action.run_recent(interval=timedelta(minutes=30))
    # routine_action.run_by_last_edited_time(datetime(2024, 1, 7, 17, 0, 0, tzinfo=my_tz), None)
    # routine_action.run_from_last_success(update_last_success_time=True)
    pass

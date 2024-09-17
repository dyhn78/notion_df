from __future__ import annotations

from workflow import backup_dir
from workflow.action.match import MatchActionBase, MatchDatei, MatchRecordDatei, \
    MatchRecordWeekiByDatei, MatchRecordTimestr, MatchReadingStartDatei, MatchEventProgress, MatchRecordDateiSchedule, \
    MatchEventProgressDatei
from workflow.action.media_scrap import MediaScrapAction
from workflow.action.migration_backup import MigrationBackupLoadAction, MigrationBackupSaveAction
from workflow.block import DatabaseEnum, schedule, start
from workflow.core.action import CompositeAction

base = MatchActionBase()
routine_action = CompositeAction([
    MigrationBackupLoadAction(backup_dir),
    MigrationBackupSaveAction(backup_dir),

    MatchDatei(base),

    MatchEventProgress(base, DatabaseEnum.issue_db),
    MatchEventProgress(base, DatabaseEnum.reading_db),
    MatchRecordDatei(base, DatabaseEnum.event_db, DatabaseEnum.datei_db.title),
    MatchRecordDatei(base, DatabaseEnum.event_db, schedule, read_datei_from_title=True, prepend_datei_on_title=True),
    MatchRecordDateiSchedule(base, DatabaseEnum.event_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.event_db, schedule, schedule),
    MatchRecordTimestr(base, DatabaseEnum.event_db, schedule),
    MatchEventProgressDatei(base, DatabaseEnum.issue_db),
    MatchEventProgressDatei(base, DatabaseEnum.reading_db),

    MatchRecordDatei(base, DatabaseEnum.journal_db, DatabaseEnum.datei_db.title,
                     read_datei_from_title=True, prepend_datei_on_title=True),
    MatchRecordWeekiByDatei(base, DatabaseEnum.journal_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDatei(base, DatabaseEnum.idea_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.idea_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDatei(base, DatabaseEnum.stage_db, DatabaseEnum.datei_db.title),
    MatchRecordDatei(base, DatabaseEnum.stage_db, schedule,
                     read_datei_from_title=True, prepend_datei_on_title=True),
    MatchRecordDateiSchedule(base, DatabaseEnum.stage_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.stage_db, schedule, schedule),

    MatchRecordDatei(base, DatabaseEnum.issue_db, DatabaseEnum.datei_db.title),
    MatchRecordDatei(base, DatabaseEnum.issue_db, schedule, read_datei_from_created_time=False, read_datei_from_title=True),
    MatchRecordDateiSchedule(base, DatabaseEnum.issue_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.issue_db, schedule, schedule),

    MatchRecordDatei(base, DatabaseEnum.reading_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),
    MatchRecordDatei(base, DatabaseEnum.reading_db, schedule, read_datei_from_created_time=False,
                     read_datei_from_title=True),
    MatchReadingStartDatei(base),
    MatchRecordDateiSchedule(base, DatabaseEnum.reading_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, start, start),

    MatchRecordDatei(base, DatabaseEnum.area_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.area_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDatei(base, DatabaseEnum.resource_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.resource_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MediaScrapAction(create_window=False),
])

if __name__ == '__main__':
    from datetime import timedelta

    # import sys
    # from loguru import logger
    # logger.remove()
    # logger.add(sys.stderr, level="TRACE")

    # routine_action.run_recent(interval=timedelta(minutes=240))
    # routine_action.run_by_last_edited_time(datetime(2024, 1, 7, 17, 0, 0, tzinfo=my_tz), None)
    routine_action.run_from_last_success(update_last_success_time=False)

from __future__ import annotations

from app import backup_dir
from app.action.match import MatchActionBase, MatchDatei, \
    MatchRecordWeekiByDatei, MatchRecordTimestr, MatchReadingStartDatei, MatchEventProgress, \
    CopyRecordDateiScheduleToDatei, \
    CopyEventProgressRels, MatchRecordDateiByLastEditedTime, MatchRecordDateiByCreatedTime, \
    MatchRecordDateiByTitle, PrependDateiOnRecordTitle
from app.action.media_scrap.main import MediaScrapAction
from app.action.migration_backup import MigrationBackupLoadAction, MigrationBackupSaveAction
from app.core.action import CompositeAction
from app.my_block import DatabaseEnum, schedule, start, thread_needs_sch_datei_prop, progress

base = MatchActionBase()
routine_action = CompositeAction([
    MigrationBackupLoadAction(backup_dir),
    MigrationBackupSaveAction(backup_dir),

    MatchDatei(base),

    MatchRecordDateiByTitle(base, DatabaseEnum.journal_db, DatabaseEnum.datei_db.title),
    MatchRecordDateiByCreatedTime(base, DatabaseEnum.journal_db, DatabaseEnum.datei_db.title),
    PrependDateiOnRecordTitle(base, DatabaseEnum.journal_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.journal_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchEventProgress(base, DatabaseEnum.thread_db),
    MatchEventProgress(base, DatabaseEnum.reading_db),
    MatchRecordDateiByCreatedTime(base, DatabaseEnum.event_db, DatabaseEnum.datei_db.title),
    MatchRecordDateiByTitle(base, DatabaseEnum.event_db, progress),
    MatchRecordDateiByCreatedTime(base, DatabaseEnum.event_db, progress, only_if_empty=True),
    PrependDateiOnRecordTitle(base, DatabaseEnum.event_db, progress),
    CopyRecordDateiScheduleToDatei(base, DatabaseEnum.event_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.event_db, progress, DatabaseEnum.datei_db.title),
    MatchRecordTimestr(base, DatabaseEnum.event_db, progress),
    CopyEventProgressRels(base, DatabaseEnum.thread_db),
    CopyEventProgressRels(base, DatabaseEnum.reading_db),

    MatchRecordDateiByCreatedTime(base, DatabaseEnum.idea_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.idea_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDateiByCreatedTime(base, DatabaseEnum.stage_db, DatabaseEnum.datei_db.title),
    MatchRecordDateiByTitle(base, DatabaseEnum.stage_db, schedule),
    MatchRecordDateiByCreatedTime(base, DatabaseEnum.stage_db, schedule, only_if_empty=True,
                                  only_if_this_checkbox_filled=thread_needs_sch_datei_prop),
    PrependDateiOnRecordTitle(base, DatabaseEnum.stage_db, schedule),
    CopyRecordDateiScheduleToDatei(base, DatabaseEnum.stage_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.stage_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.stage_db, schedule, schedule),

    MatchRecordDateiByCreatedTime(base, DatabaseEnum.thread_db, DatabaseEnum.datei_db.title),
    MatchRecordDateiByTitle(base, DatabaseEnum.thread_db, schedule),
    CopyRecordDateiScheduleToDatei(base, DatabaseEnum.thread_db),
    MatchRecordWeekiByDatei(base, DatabaseEnum.thread_db, schedule, schedule),

    MatchRecordDateiByCreatedTime(base, DatabaseEnum.reading_db, DatabaseEnum.datei_db.title),
    MatchRecordDateiByTitle(base, DatabaseEnum.reading_db, schedule),
    CopyRecordDateiScheduleToDatei(base, DatabaseEnum.reading_db),
    MatchReadingStartDatei(base),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.reading_db, start, start),

    MatchRecordDateiByCreatedTime(base, DatabaseEnum.view_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.view_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDateiByCreatedTime(base, DatabaseEnum.gist_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.gist_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MatchRecordDateiByTitle(base, DatabaseEnum.genai_db, DatabaseEnum.datei_db.title),
    MatchRecordDateiByCreatedTime(base, DatabaseEnum.genai_db, DatabaseEnum.datei_db.title),
    MatchRecordDateiByLastEditedTime(base, DatabaseEnum.genai_db, DatabaseEnum.datei_db.title),
    PrependDateiOnRecordTitle(base, DatabaseEnum.genai_db, DatabaseEnum.datei_db.title),
    MatchRecordWeekiByDatei(base, DatabaseEnum.genai_db, DatabaseEnum.weeki_db.title, DatabaseEnum.datei_db.title),

    MediaScrapAction(create_window=False),
])

if __name__ == '__main__':
    # import sys
    # from loguru import logger
    # logger.remove()
    # logger.add(sys.stderr, level="TRACE")

    # routine_action.run_recent(interval=timedelta(minutes=240))
    # routine_action.run_by_last_edited_time(datetime(2024, 1, 7, 17, 0, 0, tzinfo=my_tz), None)
    routine_action.run_from_last_success(update_last_success_time=True)

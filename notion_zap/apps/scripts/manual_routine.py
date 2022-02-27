from notion_zap.apps.media_scraper import \
    ReadingTableStatusResolver, ReadingTableDuplicateRemover
from notion_zap.apps.prop_matcher.controllers.build_calendar import CalendarBuildController
from notion_zap.apps.prop_matcher.controllers.resolve_sync import SyncResolveController

CalendarBuildController(fetch_empties=True).execute()
ReadingTableDuplicateRemover().execute(request_size=0)
ReadingTableStatusResolver().execute()
SyncResolveController(date_range=0).execute()

close_program = input("작업 완료. 아무 키나 누르십시오...")

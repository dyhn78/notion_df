from notion_zap.apps.media_scraper import \
    ReadingDBStatusResolver, ReadingDBDuplicateRemover
from notion_zap.apps.prop_matcher.build_calendar import CalendarController
from notion_zap.apps.prop_matcher.resolve_sync import PropertySyncResolver

CalendarController(fetch_empties=True).execute()
ReadingDBDuplicateRemover().execute(request_size=0)
ReadingDBStatusResolver().execute()
PropertySyncResolver(date_range=0).execute()

close_program = input("작업 완료. 아무 키나 누르십시오...")

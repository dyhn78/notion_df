from notion_py.interface.utility import stopwatch
from notion_py.applications.prop_matcher import PropertySyncResolver
from notion_py.applications.media_scraper import \
    ReadingDBStatusResolver, ReadingDBDuplicateRemover


ReadingDBDuplicateRemover().execute(page_size=0)
ReadingDBStatusResolver().execute()
PropertySyncResolver(date_range=0).execute()


stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

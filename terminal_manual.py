from notion_py.interface.utility import stopwatch
from notion_py.applications.prop_matcher.yearly_calendar import YearlyCalendarCreator
# from notion_py.applications.media_scraper import \
#     ReadingDBStatusResolver, ReadingDBDuplicateRemover
# from notion_py.applications.prop_matcher import PropertySyncResolver

YearlyCalendarCreator(year=2024).execute()
#
# ReadingDBDuplicateRemover().execute(request_size=0)
# ReadingDBStatusResolver().execute()
# PropertySyncResolver(date_range=0).execute()

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

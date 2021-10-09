from notion_py.interface.utility import stopwatch
from notion_py.applications.prop_matcher import PropertyMatcher
from notion_py.applications.media_scraper import ReadingDBRegularScraper

PropertyMatcher(date_range=30).execute()
ReadingDBRegularScraper().execute(page_size=5)

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

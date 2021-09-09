from notion_py.interface.utility import stopwatch
from notion_py.applications.log_editor import DateMatcher
from notion_py.applications.media_scraper import MediaScraper

DateMatcher(date_range=7).execute()
# MediaScraper().execute(3)

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

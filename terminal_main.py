from notion_py.applications.media_scraper import ReadingDBScrapController
from notion_py.applications.prop_matcher import MatchController
from notion_py.interface.utility import stopwatch

ReadingDBScrapController().execute(request_size=5)
MatchController(date_range=7).execute()

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

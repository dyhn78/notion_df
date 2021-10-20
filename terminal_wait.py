from notion_py.applications.media_scraper.regular_scrap import ReadingDBScrapController
from notion_py.interface.utility import stopwatch

ReadingDBScrapController(tasks={'bookstore'}, title='눈치').execute(request_size=3)

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

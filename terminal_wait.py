from notion_py.applications.media_scraper.regular_scrap import ReadingDBScrapController
from notion_py.interface.utility import stopwatch

ReadingDBScrapController(tasks={'bookstore'}, title='대서울길').execute(request_size=1)

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

from notion_py.applications.media_scraper.regular_scrap import ReadingDBRegularScraper
from notion_py.interface.utility import stopwatch

# ReadingDBRegularScraper().execute(page_size=0)
ReadingDBRegularScraper(
    targets={}, title='').execute(page_size=0)

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

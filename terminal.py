from notion_py.applications.log_editor.endpoint import match_with_dates, match_with_periods
from notion_py.applications.read_scraper import regular_read_scraper
from notion_py.helpers import stopwatch

match_with_dates(check_only_past_x_days=7)
match_with_periods(check_only_past_x_days=7)
regular_read_scraper(page_size=0)

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

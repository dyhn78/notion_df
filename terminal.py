from notion_py.applications.log_editor.endpoint import update_dates, update_periods
from notion_py.applications.read_scraper import scrap_readings
from notion_py.utility import stopwatch

update_dates(check_only_past_x_days=7)
update_periods(check_only_past_x_days=7)
# scrap_readings(page_size=0)

stopwatch('작업 완료')
# close_program = input("작업 완료. 아무 키나 누르십시오...")

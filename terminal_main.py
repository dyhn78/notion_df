from notion_zap.cli.utility import stopwatch
from notion_zap.apps.media_scraper import ReadingDBScrapController
from notion_zap.apps.prop_matcher import MatchController

MatchController(date_range=7).execute()
ReadingDBScrapController().execute(request_size=5)

stopwatch('모든 작업 완료')

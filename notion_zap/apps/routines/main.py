from notion_zap.cli.utility import stopwatch
from notion_zap.apps.prop_matcher.regulars import RegularMatchController
from notion_zap.apps.media_scraper import ReadingDBScrapController


def execute():
    RegularMatchController().execute()
    ReadingDBScrapController().execute(request_size=5)

    stopwatch('모든 작업 완료')

from notion_zap.apps.media_scraper.controllers.scrap_regulars import RegularScrapController
from notion_zap.apps.prop_matcher.controllers.match_regulars import MatchController
from notion_zap.apps.helpers.deal_exception import deal_exception_with_logs
from notion_zap.cli.utility import stopwatch


@deal_exception_with_logs
def main():
    controller = MatchController()
    controller(request_size=20)
    controller = RegularScrapController(targets={'metadata', 'gy'})
    controller(request_size=5)
    stopwatch('모든 작업 완료')


if __name__ == '__main__':
    main()
    # x = input("아무 키나 누르십시오...")

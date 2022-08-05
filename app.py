from notion_zap.apps.helpers.deal_exception import ExceptionLogger
from notion_zap.apps.media_scraper.controllers.scrap_regulars import RegularScrapController
from notion_zap.apps.prop_matcher.controllers.match_regulars import MatchController
from notion_zap.cli.utility import stopwatch


@ExceptionLogger()
def main():
    controller = MatchController()
    controller(request_size=20)
    print('='*40)
    controller = RegularScrapController(targets={'metadata', 'gy'})
    controller(request_size=5)


if __name__ == '__main__':
    main()
    stopwatch('모든 작업 완료')
    # x = input("아무 키나 누르십시오...")

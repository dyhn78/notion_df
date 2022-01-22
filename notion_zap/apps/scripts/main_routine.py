from notion_zap.cli.utility import stopwatch
from notion_zap.apps.prop_matcher.match_regulars import RegularMatchController
from notion_zap.apps.media_scraper import RegularScrapController
import traceback
import datetime as dt


def main():
    message = f"last execution: {dt.datetime.now()}"+"\n"
    try:

        controller = RegularMatchController()
        controller.execute(request_size=20)

        controller = RegularScrapController()
        controller.execute(request_size=5)

        with open('debug.log', 'a', encoding='utf-8') as log:
            log.write(message)
        stopwatch('모든 작업 완료')
    except Exception as err:
        with open('debug.log', 'w', encoding='utf-8') as log:
            log.write(message+'\n')
            traceback.print_exc(file=log)
        raise err


if __name__ == '__main__':
    main()

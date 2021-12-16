from notion_zap.cli.utility import stopwatch
from notion_zap.apps.prop_matcher.match_regulars import RegularMatchController
from notion_zap.apps.media_scraper import RegularScrapController
import traceback
import datetime as dt


def main():
    log = open('debug.log', 'w', encoding='utf-8')
    log.write(f"last execution: {dt.datetime.now()}")
    try:
        RegularMatchController().execute(request_size=20)
        RegularScrapController().execute(request_size=5)

        stopwatch('모든 작업 완료')
    except Exception as err:
        traceback.print_exc(file=log)
        log.close()
        raise err


if __name__ == '__main__':
    main()

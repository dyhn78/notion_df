import traceback
import datetime as dt

from notion_zap.cli.utility import stopwatch
from notion_zap.apps.media_scraper.controllers.scrap_regulars import \
    RegularScrapController
from notion_zap.apps.prop_matcher.controllers.match_regulars import \
    RegularMatchController


def main_logic():
    controller = RegularMatchController()
    controller(request_size=20)
    controller = RegularScrapController(targets={'metadata', 'gy'})
    controller(request_size=5)
    stopwatch('모든 작업 완료')


def deal_exception_with_breakpoint():
    # noinspection PyBroadException
    # try:
    #     main_logic()
    # except:
    #     traceback.print_exc()
    #     breakpoint()
    main_logic()


def deal_exception_with_logs():
    message = f"last execution: {dt.datetime.now()}"+"\n"
    try:
        main_logic()
        with open('debug.log', 'a', encoding='utf-8') as log:
            log.write(message)
    except Exception as err:
        with open('debug.log', 'w', encoding='utf-8') as log:
            log.write(message+'\n'*1)
            traceback.print_exc(file=log)
            log.write('\n'*3)
        raise err


if __name__ == '__main__':
    deal_exception_with_breakpoint()

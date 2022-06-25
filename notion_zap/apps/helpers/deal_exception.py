import datetime as dt
import traceback
from typing import Callable


def deal_exception_with_breakpoint(func: Callable):
    def wrapper(*args):
        # noinspection PyBroadException
        # try:
        #     main_logic()
        # except:
        #     traceback.print_exc()
        #     breakpoint()
        func(*args)

    return wrapper


def deal_exception_with_logs(func: Callable):
    def wrapper(*args):
        message = f"last execution: {dt.datetime.now()}"+"\n"
        try:
            func(*args)
            with open('debug.log', 'a', encoding='utf-8') as log:
                log.write(message)
        except Exception as err:
            with open('debug.log', 'w', encoding='utf-8') as log:
                log.write(message+'\n'*1)
                traceback.print_exc(file=log)
                log.write('\n'*3)
            raise err

    return wrapper

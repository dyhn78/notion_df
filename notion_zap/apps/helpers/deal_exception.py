import datetime as dt
import traceback
from typing import Callable

from notion_zap.cli.editors import Root, TextItem

LOG_DEST_ID = '6d16dc6747394fca95dc169c8c736e2d'
MY_USER_ID = 'a007d150-bc67-422c-87db-030a71867dd9'


def deal_exception_with_breakpoint(func: Callable) -> Callable:
    def wrapper(*args):
        # noinspection PyBroadException
        # try:
        #     main_logic()
        # except:
        #     traceback.print_exc()
        #     breakpoint()
        func(*args)

    return wrapper


def deal_exception_with_logs(func: Callable) -> Callable:
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


class ExceptionLogger:
    def __init__(self):
        self.root = Root()
        log_page = self.root.space.page_item(LOG_DEST_ID, "[NP.log] 서버 로그")
        log_page.children.fetch()
        for child in log_page.children[:-30]:
            child.archive()
        log_page.save()
        self.log_block = log_page.children.open_new_text()
        self.log_contents = self.log_block.write_rich_paragraph()

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args):
            message = f"last execution: {dt.datetime.now()}"
            try:
                func(*args)
            except Exception as err:
                with open('debug.log', 'w+', encoding='utf-8') as log_file:
                    traceback.print_exc(file=log_file)
                    log_file.seek(0)
                    message += log_file.read()
                self.log_contents.mention_user(MY_USER_ID)
                self.log_contents.write_text('\n')
                raise err
            finally:
                self.log_contents.write_text(message)
                self.log_block.save()

        return wrapper

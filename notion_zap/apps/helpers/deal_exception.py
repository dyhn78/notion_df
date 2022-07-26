import datetime as dt
import traceback
from typing import Callable
import pytz

from notion_zap.cli.editors import Root

LOCAL_TIMEZONE = pytz.timezone('Asia/Seoul')
LOG_DEST_ID = '6d16dc6747394fca95dc169c8c736e2d'
MY_USER_ID = 'a007d150-bc67-422c-87db-030a71867dd9'


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
            start_time = dt.datetime.now()
            time_message = f"last execution: {start_time.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}"
            traceback_message = ""
            try:
                func(*args)
            except Exception as err:
                self.log_contents.mention_user(MY_USER_ID)
                with open('debug.log', 'w+', encoding='utf-8') as log_file:
                    traceback.print_exc(file=log_file)
                    log_file.seek(0)
                    traceback_message = log_file.read()
                raise err
            finally:
                time_elapsed = dt.datetime.now() - start_time
                time_message += f" ({str(time_elapsed)}"
                self.log_contents.write_text('\n'.join([time_message, traceback_message]))
                self.log_block.save()

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

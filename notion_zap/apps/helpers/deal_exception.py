import datetime as dt
import traceback
from json import JSONDecodeError
from typing import Callable

import pytz

from notion_zap.cli.blocks import TextItem
from notion_zap.cli.core.base import Root
from notion_zap.cli.utility import stopwatch

LOCAL_TIMEZONE = pytz.timezone('Asia/Seoul')
LOG_DEST_ID = '6d16dc6747394fca95dc169c8c736e2d'
MY_USER_ID = 'a007d150-bc67-422c-87db-030a71867dd9'


class ExceptionLogger:
    def __init__(self):
        self.root = Root()
        self.log_page = self.root.space.page_item(LOG_DEST_ID, "[NP.log] 서버 로그")
        self.log_page.children.fetch()
        self.log_block = self.log_page.children.open_new_text()
        self.log_contents = self.log_block.write_rich_paragraph()

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args):
            start_time = dt.datetime.now()
            time_message = f"last execution: {start_time.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}"
            traceback_message = ""
            try:
                func(*args)
                for child in self.log_page.children[:-30]:
                    child.requestor.delete()
                # log_page.save() -- TODO
            except JSONDecodeError as err:
                traceback_message = f"failed - {err}"
            except Exception as err:
                for child in self.log_page.children:
                    child: TextItem
                    if child.block_id:
                        child.requestor.delete()
                self.log_contents.mention_user(MY_USER_ID)
                self.log_contents.write_text('\n')
                with open('debug.log', 'w+', encoding='utf-8') as log_file:
                    traceback.print_exc(file=log_file)
                    log_file.seek(0)
                    traceback_message = log_file.read()
                raise err
            finally:
                delta = dt.datetime.now() - start_time
                time_message += f" ({delta.seconds}.{str(delta.microseconds)[:3]} seconds)"
                if len(traceback_message) > 1800:
                    traceback_message = traceback_message[:800] + "\n\n...\n\n" + traceback_message[-1000:]
                self.log_contents.write_text((time_message + " " + traceback_message).strip())
                self.log_block.save()
                stopwatch('모든 작업 완료')

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

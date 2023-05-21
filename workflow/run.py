import json
import traceback
from datetime import datetime, timedelta
from typing import Callable, Any
from uuid import UUID

from notion_df.entity import Block
from notion_df.object.block import CodeBlockValue, ParagraphBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.variable import my_tz, Settings
from workflow.action.prop_matcher import MatchActionBase, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByRefDate, MatchReadingsStartDate
from workflow.action.reading_media_scraper import MediaScraper
from workflow.constant.block_enum import DatabaseEnum
from workflow.util.action import Action, get_last_edited_time_lower_bound

# Note: the log_page is implemented as page with log blocks, not database with log pages,
#  since Notion API does not directly support permanently deleting pages,
#  and third party solutions like https://github.com/pocc/bulk_delete_notion_pages needs additional works to integrate.
my_user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')
log_page_id = '6d16dc6747394fca95dc169c8c736e2d'
log_page_block = Block(log_page_id)
log_date_format = r'%Y-%m-%d %H:%M:%S'


class Workflow:
    def __init__(self, print_body: bool, create_window: bool):
        self.print_body = print_body
        workspace = MatchActionBase()
        self.actions: list[Action] = [
            MatchWeekByDateValue(workspace),

            MatchDateByCreatedTime(workspace, DatabaseEnum.event_db, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.event_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.event_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.issue_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.issue_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.journal_db, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.journal_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.journal_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.note_db, '시작'),
            MatchWeekByRefDate(workspace, DatabaseEnum.note_db, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.topic_db, '시작'),
            MatchWeekByRefDate(workspace, DatabaseEnum.topic_db, '시작', '시작'),

            MatchReadingsStartDate(workspace),
            MatchDateByCreatedTime(workspace, DatabaseEnum.reading_db, '생성'),
            MatchWeekByRefDate(workspace, DatabaseEnum.reading_db, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.section_db, '시작'),
            MatchWeekByRefDate(workspace, DatabaseEnum.section_db, '시작', '시작'),

            # TODO 배포후: <마디 - 🟢시작, 💚시작> 제거
            # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)

            MediaScraper(create_window),
        ]

    def execute_all(self):
        with Settings.print.enable(self.print_body):
            for action in self.actions:
                action.execute_all()

    def execute_recent(self, custom_window: timedelta):
        with Settings.print.enable(self.print_body):
            last_edited_time_lower_bound = get_last_edited_time_lower_bound(custom_window)
            Action.execute_recent(self.actions, last_edited_time_lower_bound)

    @staticmethod
    def _run(execute: Callable[[], Any]):
        def format_time() -> str:
            execution_time = datetime.now().astimezone(my_tz) - start_time
            execution_datetime = datetime(1, 1, 1) + execution_time
            execution_time_str = execution_datetime.strftime('%S.%f')
            return f'{start_time_str} - {execution_time_str} seconds'

        start_time = datetime.now().astimezone(my_tz)
        start_time_str = f"{start_time.strftime(log_date_format)}"
        child_block_values = []
        try:
            execute()
            message = f"success - {format_time()}"
            child_block_values = [ParagraphBlockValue(RichText([TextSpan(message)]))]
        except json.JSONDecodeError as err:
            message = f"failure - {format_time()}: {err}"
            child_block_values = [ParagraphBlockValue(RichText([TextSpan(message)]))]
        except (Exception, RecursionError) as e:
            message = f"error - {format_time()}: "
            tr = traceback.format_exc()
            child_block_values = [
                ParagraphBlockValue(RichText([TextSpan(message), UserMention(my_user_id)])),
            ]
            for i in range(0, len(tr), 1000):
                child_block_values.append(CodeBlockValue(RichText.from_plain_text(tr[i:i + 1000])))
            raise e
        finally:
            children = log_page_block.retrieve_children()
            for child in children[3:]:
                if isinstance(child.value, ParagraphBlockValue) and \
                        start_time - child.created_time > timedelta(days=1):
                    child.delete()
            log_page_block.append_children(child_block_values)

    def run_all(self):
        self._run(self.execute_all)

    def run_recent(self, custom_window: timedelta):
        self._run(lambda: self.execute_recent(custom_window))

    def run_window(self):
        with Settings.print.enable(self.print_body):
            for block in reversed(log_page_block.retrieve_children()):
                if not isinstance(block.value, ParagraphBlockValue):
                    continue
                block_created_time_str = block.value.rich_text.plain_text
                if block_created_time_str.find('success') == -1:
                    continue
                # last_edited_time_lower_bound = min(
                #     datetime.strptime(block_created_time_str.split(' - ')[1], log_date_format).astimezone(my_tz),
                #     get_last_edited_time_lower_bound(timedelta(minutes=10)))
                last_edited_time_lower_bound = (
                    datetime.strptime(block_created_time_str.split(' - ')[1], log_date_format).astimezone(my_tz))
                                                   
                self._run(lambda: Action.execute_recent(self.actions, last_edited_time_lower_bound))
                return
            self.run_all()


if __name__ == '__main__':
    Workflow(print_body=True, create_window=False).run_window()

import json
import traceback
from datetime import datetime, timedelta
from uuid import UUID

from notion_df.entity import Page
from notion_df.object.block import CodeBlockValue, ParagraphBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.variable import my_tz, Settings
from workflow.action.prop_matcher import MatcherWorkspace, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByDate, MatchReadingsStartDate
from workflow.action.reading_media_scraper import MediaScraper
from workflow.constant.block_enum import DatabaseEnum
from workflow.util.action import Action

log_page_id = '6d16dc6747394fca95dc169c8c736e2d'
my_user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')


class Workflow:
    def __init__(self, print_body: bool, create_window: bool):
        self.print_body = print_body
        workspace = MatcherWorkspace()
        self.actions: list[Action] = [
            MatchWeekByDateValue(workspace),

            MatchDateByCreatedTime(workspace, DatabaseEnum.event_db, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.event_db, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.event_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.issue_db, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.issue_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.journal_db, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.journal_db, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.journal_db, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.note_db, '시작'),
            MatchWeekByDate(workspace, DatabaseEnum.note_db, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.topic_db, '시작'),
            MatchWeekByDate(workspace, DatabaseEnum.topic_db, '시작', '시작'),

            MatchReadingsStartDate(workspace),
            MatchDateByCreatedTime(workspace, DatabaseEnum.reading_db, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.reading_db, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.section_db, '시작'),
            MatchWeekByDate(workspace, DatabaseEnum.section_db, '시작', '시작'),

            # TODO 배포후: <마디 - 🟢시작, 💚시작> 제거
            # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)

            MediaScraper(create_window),
        ]

    def execute(self):
        if self.print_body:
            Settings.print_body.enabled = True
        for action in self.actions:
            action.execute()
        Settings.print_body.enabled = False

    # noinspection PyBroadException
    def run(self):
        execution_time = f"{datetime.now().astimezone(my_tz).strftime('%Y-%m-%d %H:%M:%S')}"
        child_block_values = []
        try:
            self.execute()
            message = f"{execution_time} - success"
            child_block_values = [ParagraphBlockValue(RichText([TextSpan(message)]))]
        except json.JSONDecodeError as err:
            message = f"{execution_time} - failure: {err}"
            child_block_values = [ParagraphBlockValue(RichText([TextSpan(message)]))]
        except (Exception, RecursionError) as e:
            message = f"{execution_time} - error: "
            tr = traceback.format_exc()
            child_block_values = [
                ParagraphBlockValue(RichText([TextSpan(message), UserMention(my_user_id)])),
            ]
            for i in range(0, len(tr), 1000):
                child_block_values.append(CodeBlockValue(RichText.from_plain_text(tr[i:i + 1000])))
            raise e
        finally:
            log_page_block = Page(log_page_id).as_block()
            children = log_page_block.retrieve_children()
            for child in children:
                if datetime.now() - child.created_time > timedelta(days=1):
                    child.delete()
            log_page_block.append_children(child_block_values)


if __name__ == '__main__':
    Workflow(print_body=True, create_window=False).execute()

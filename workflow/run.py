import datetime as dt
import json
import traceback
from uuid import UUID

from notion_df.entity import Namespace
from notion_df.object.block import CodeBlockValue, ParagraphBlockValue
from notion_df.object.rich_text import RichText, TextSpan, UserMention
from notion_df.variable import my_tz
from workflow.action.prop_matcher import MatcherWorkspace, MatchWeekByDateValue, MatchDateByCreatedTime, \
    MatchWeekByDate, MatchReadingsStartDate
from workflow.constant.block_enum import DatabaseEnum
from workflow.util.action import Action

log_page_id = '6d16dc6747394fca95dc169c8c736e2d'
my_user_id = UUID('a007d150-bc67-422c-87db-030a71867dd9')


class Workflow:
    def __init__(self, print_body: bool, create_window: bool):
        self.namespace = Namespace(print_body=print_body)
        workspace = MatcherWorkspace(self.namespace)
        self.actions: list[Action] = [
            # TODO
            # ReadingMediaScraper(self.namespace, create_window),

            MatchWeekByDateValue(workspace),

            MatchDateByCreatedTime(workspace, DatabaseEnum.events, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.events, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.events, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.issues, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.issues, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.journals, '일간'),
            MatchDateByCreatedTime(workspace, DatabaseEnum.journals, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.journals, '주간', '일간'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.notes, '시작'),
            MatchWeekByDate(workspace, DatabaseEnum.notes, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.topics, '시작'),
            MatchWeekByDate(workspace, DatabaseEnum.topics, '시작', '시작'),

            MatchReadingsStartDate(workspace),
            MatchDateByCreatedTime(workspace, DatabaseEnum.readings, '생성'),
            MatchWeekByDate(workspace, DatabaseEnum.readings, '시작', '시작'),

            MatchDateByCreatedTime(workspace, DatabaseEnum.sections, '시작'),
            MatchWeekByDate(workspace, DatabaseEnum.sections, '시작', '시작'),

            # TODO 배포후: <마디 - 🟢시작, 💚시작> 제거
            # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)
        ]

    # noinspection PyBroadException
    def execute(self):
        execution_time = f"{dt.datetime.now().astimezone(my_tz).strftime('%Y-%m-%d %H:%M:%S')}"
        child_block_values = []
        try:
            for action in self.actions:
                action.execute()
            message = f"{execution_time} - success"
            child_block_values = [ParagraphBlockValue(RichText([TextSpan(message)]))]
        except json.JSONDecodeError as err:
            message = f"{execution_time} - failure: {err}"
            child_block_values = [ParagraphBlockValue(RichText([TextSpan(message)]))]
        except Exception as e:
            message = f"{execution_time} - error: "
            tr = traceback.format_exc()
            child_block_values = [
                ParagraphBlockValue(RichText([TextSpan(message), UserMention(my_user_id)])),
            ]
            for i in range(0, len(tr), 1000):
                child_block_values.append(CodeBlockValue(RichText.from_plain_text(tr[i:i + 1000])))
            raise e
        finally:
            log_page_block = self.namespace.page(log_page_id).as_block()
            log_page_block.append_children(child_block_values)
            children = log_page_block.retrieve_children()
            for child in children[:-30]:
                child.delete()


if __name__ == '__main__':
    Workflow(print_body=True, create_window=True).execute()

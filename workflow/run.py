from notion_df.entity import Namespace
from workflow.action.prop_matcher import MatchDateByCreatedTime, MatchWeekByDate, Action, \
    MatchWeekByDateValue, MatchReadingsStartDate, MatcherWorkspace
from workflow.util.block_enum import DatabaseEnum

if __name__ == '__main__':
    workspace = MatcherWorkspace(Namespace(print_body=True))
    actions: list[Action] = [
        MatchWeekByDateValue(workspace),

        MatchDateByCreatedTime(workspace, DatabaseEnum.events, '일간'),
        MatchDateByCreatedTime(workspace, DatabaseEnum.events, '생성'),
        MatchWeekByDate(workspace, DatabaseEnum.events, '주간', '일간'),

        MatchDateByCreatedTime(workspace, DatabaseEnum.issues, '시작'),
        MatchWeekByDate(workspace, DatabaseEnum.issues, '시작', '시작'),

        MatchDateByCreatedTime(workspace, DatabaseEnum.journals, '일간'),
        MatchDateByCreatedTime(workspace, DatabaseEnum.journals, '생성'),
        MatchWeekByDate(workspace, DatabaseEnum.journals, '주간', '일간'),

        MatchDateByCreatedTime(workspace, DatabaseEnum.notes, '일간'),  # TODO 배포후: 시작
        MatchWeekByDate(workspace, DatabaseEnum.notes, '주간', '일간'),  # TODO 배포후: 시작, 시작

        MatchDateByCreatedTime(workspace, DatabaseEnum.topics, '시작'),
        MatchWeekByDate(workspace, DatabaseEnum.topics, '시작', '시작'),

        MatchReadingsStartDate(workspace),
        MatchDateByCreatedTime(workspace, DatabaseEnum.readings, '생성'),
        MatchWeekByDate(workspace, DatabaseEnum.readings, '시작', '시작'),

        MatchDateByCreatedTime(workspace, DatabaseEnum.sections, '시작'),
        MatchWeekByDate(workspace, DatabaseEnum.sections, '시작', '시작'),

        # TODO 배포후: <마디 - 🟢시작, 💚시작> 제거
        # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)

        # TODO 배포전:
        #  - media scraper
        #  - wrap as workflow, integrate deal_exception
    ]
    for action in actions:
        action.execute()

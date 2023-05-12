from notion_df.entity import Namespace
from workflow.action.prop_matcher import MatchDateByCreatedTime, MatchWeekByDate, Action, \
    MatchWeekByDateValue, MatchReadingsStartDate
from workflow.util.block_enum import DatabaseEnum

if __name__ == '__main__':
    namespace = Namespace(print_body=True)
    actions: list[Action] = [
        MatchWeekByDateValue(namespace),

        MatchDateByCreatedTime(namespace, DatabaseEnum.events, '일간'),
        MatchDateByCreatedTime(namespace, DatabaseEnum.events, '생성'),
        MatchWeekByDate(namespace, DatabaseEnum.events, '주간', '일간'),

        MatchDateByCreatedTime(namespace, DatabaseEnum.issues, '시작'),
        MatchWeekByDate(namespace, DatabaseEnum.issues, '시작', '시작'),

        MatchDateByCreatedTime(namespace, DatabaseEnum.journals, '일간'),
        MatchDateByCreatedTime(namespace, DatabaseEnum.journals, '생성'),
        MatchWeekByDate(namespace, DatabaseEnum.journals, '주간', '일간'),

        MatchDateByCreatedTime(namespace, DatabaseEnum.notes, '일간'),  # TODO 배포후: 시작
        MatchWeekByDate(namespace, DatabaseEnum.notes, '주간', '일간'),  # TODO 배포후: 시작, 시작

        MatchDateByCreatedTime(namespace, DatabaseEnum.topics, '시작'),
        MatchWeekByDate(namespace, DatabaseEnum.topics, '시작', '시작'),

        MatchReadingsStartDate(namespace),
        MatchDateByCreatedTime(namespace, DatabaseEnum.readings, '생성'),
        MatchWeekByDate(namespace, DatabaseEnum.readings, '시작', '시작'),

        MatchDateByCreatedTime(namespace, DatabaseEnum.sections, '시작'),
        MatchWeekByDate(namespace, DatabaseEnum.sections, '시작', '시작'),

        # TODO 배포후: <마디 - 🟢시작, 💚시작> 제거
        # TODO 배포후: <읽기 -  📕유형 <- 전개/꼭지> 추가 (스펙 논의 필요)

        # TODO 배포전:
        #  - media scraper
        #  - wrap as workflow, integrate deal_exception
    ]
    for action in actions:
        action.execute()

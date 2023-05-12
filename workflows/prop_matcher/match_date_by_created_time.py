import datetime as dt
from typing import Optional

from notion_df.entity import Namespace, Page
from notion_df.property import RelationPropertyKey, TitlePropertyKey, PageProperties, DateFormulaPropertyKey
from workflows.util.block_enum import BlockEnum
from workflows.util.emoji_code import EmojiCode

korean_weekday = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]


class MatchDateByCreatedTime:
    def __init__(self, events: BlockEnum, key_event_to_date: str):
        self.namespace = Namespace()
        self.date_namespace = DateNamespace()
        self.events = self.namespace.database(events.id)
        self.event_key_to_date = RelationPropertyKey(f'{BlockEnum.dates.prefix}{key_event_to_date}')
        self.event_key_datetime_auto = DateFormulaPropertyKey(f'{EmojiCode.TIMER}일시')

    def execute(self, print_body: bool = False):
        self.namespace.print_body = self.date_namespace.namespace.print_body = print_body

        event_list = self.events.query(self.event_key_to_date.filter.is_empty())
        for event in event_list:
            date = self.process_page(event)
            print(f'"{event.last_response.properties.title.plain_text} ({event.last_response.url})"'
                  + (f'-> "{date.last_response.properties.title.plain_text}"' if date else ': Skipped'))

    def process_page(self, event: Page) -> Optional[Page]:
        # TODO: '⏲️일시' 대신 created time, '📆일시' 등 low-level property 를 받아 직접 계산
        event_datetime_auto = event.last_response.properties[self.event_key_datetime_auto]
        event_date = (event_datetime_auto + dt.timedelta(hours=5)).date()
        date = self.date_namespace.get_by_date_value(event_date)

        # final check if the date value is meanwhile changed
        if event.retrieve().properties[self.event_key_to_date]:
            return
        event.update(PageProperties({self.event_key_to_date: self.event_key_to_date.page([date.id])}))
        return date


class DateNamespace:
    def __init__(self):
        self.namespace = Namespace()
        self.database = self.namespace.database(BlockEnum.dates.id)
        self.key_title = TitlePropertyKey(f'{EmojiCode.GREEN_BOOK}제목')
        self.pages_by_title_plain_text: dict[str, Page] = {}

    def get_by_date_value(self, date_value: dt.date) -> Page:
        day_name = korean_weekday[date_value.isoweekday() % 7]
        date_title_plain_text = f'{date_value.strftime("%y%m%d")} {day_name}'
        return self.get_by_title_plain_text(date_title_plain_text)

    def get_by_title_plain_text(self, date_title_plain_text: str) -> Page:
        if not (date := self.pages_by_title_plain_text.get(date_title_plain_text)):
            date_list = self.database.query(self.key_title.filter.equals(date_title_plain_text))
            if date_list:
                date = date_list[0]
            else:
                date = self.database.create_child_page(PageProperties({
                    self.key_title: self.key_title.page.from_plain_text(date_title_plain_text)
                }))
            self.pages_by_title_plain_text[date.last_response.properties.title.plain_text] = date
        return date


if __name__ == '__main__':
    actions = [
        MatchDateByCreatedTime(BlockEnum.events, '일간'),
        MatchDateByCreatedTime(BlockEnum.events, '생성')
    ]
    for action in actions:
        action.execute(print_body=True)

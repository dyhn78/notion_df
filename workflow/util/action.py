from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import timedelta, datetime
from pprint import pprint
from typing import Iterable

from notion_df.entity import Page, Children, search_by_title
from notion_df.variable import Settings, print_width, my_tz


class Action(metaclass=ABCMeta):
    @abstractmethod
    def query_all(self) -> Children[Page]:
        pass

    @abstractmethod
    def pick(self, pages: list[Page]) -> Iterable[Page]:
        """from given retrieved pages, pick the ones which need to process."""
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]):
        pass

    def execute_all(self):
        self.process(self.query_all())

    @classmethod
    def execute_recent(cls, actions: list[Action], min_last_edited_time: datetime):
        recent_pages = search_recently_changed_pages(min_last_edited_time)
        for self in actions:
            self.process(self.pick(recent_pages))


def get_last_edited_time_lower_bound(window: timedelta) -> datetime:
    # Note: Notion APIs' last_edited_time info is only with minutes resolution
    return datetime.now().astimezone(my_tz) - window


# TODO: integrate with base function
def search_recently_changed_pages(last_edited_time_lower_bound: datetime) -> list[Page]:
    last_edited_time_lower_bound = last_edited_time_lower_bound.replace(second=0, microsecond=0)
    pages = []
    try:
        while True:
            for page in search_by_title('', 'page'):
                if page.last_edited_time < last_edited_time_lower_bound:
                    return pages
                pages.append(page)
    finally:
        if Settings.print.enabled:
            pprint(pages, width=print_width)

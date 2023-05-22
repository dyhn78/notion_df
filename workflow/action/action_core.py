from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from pprint import pprint
from typing import Iterable, Optional

from notion_df.entity import Page, Children, search_by_title
from notion_df.variable import Settings, print_width, my_tz

upper_bound_timedelta = timedelta(seconds=30)


class Action(metaclass=ABCMeta):
    @abstractmethod
    def query_all(self) -> Children[Page]:
        pass

    @abstractmethod
    def filter(self, record: Page) -> bool:
        """from given retrieved pages, pick the ones which need to process."""
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]):
        pass

    def execute_all(self):
        self.process(self.query_all())

    @classmethod
    def execute_by_last_edited_time(cls, actions: list[Action], lower_bound: datetime,
                                    upper_bound: Optional[datetime] = None):
        if upper_bound is None:
            upper_bound = datetime.now().astimezone(my_tz) - upper_bound_timedelta
        recent_pages = search_pages_by_last_edited_time(lower_bound, upper_bound)
        for self in actions:
            self.process(page for page in recent_pages if self.filter(page))


def search_pages_by_last_edited_time(lower_bound: datetime, upper_bound: Optional[datetime] = None) -> list[Page]:
    # TODO: integrate with base function
    # Note: Notion APIs' last_edited_time info is only with minutes resolution
    lower_bound = lower_bound.replace(second=0, microsecond=0)
    print(lower_bound.isoformat(), upper_bound.isoformat())
    pages = []
    for page in search_by_title('', 'page'):
        if upper_bound is not None and page.last_edited_time > upper_bound:
            continue
        if page.last_edited_time < lower_bound:
            break
        pages.append(page)
    if Settings.print.enabled:
        pprint(pages, width=print_width)
    return pages

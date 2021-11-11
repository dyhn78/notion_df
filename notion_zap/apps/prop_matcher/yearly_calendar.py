from datetime import date as dateclass, timedelta

from notion_zap.cli import editors
from .common.base import LocalBase
from .common.date_index import DateHandler
from .matchers.match_to_periods import PeriodMatcherType1


class YearlyCalendarCreator:
    def __init__(self, year: int):
        self.root = editors.RootEditor()
        self.bs = LocalBase()

        self.year = year
        min_year = self.year
        max_year = self.year + 1
        self.min_date = dateclass(min_year, 1, 1)
        self.max_date = dateclass(max_year, 1, 1)

    def execute(self):
        self.make_query()
        DatePagesCreator(self.bs, self.min_date, self.max_date).execute()
        self.bs.dates.save()
        PeriodMatcherType1(self.bs).execute()
        self.bs.save()

    def make_query(self):
        query = self.bs.dates.open_query()
        frame = query.filter_maker.date_at('manual_date')
        ft = frame.on_or_after(self.min_date)
        ft &= frame.before(self.max_date)
        query.push_filter(ft)
        query.execute()
        if not self.bs.dates.list_all():
            self.bs.dates.fetch(1)

        query = self.bs.periods.open_query()
        frame = query.filter_maker.date_at('manual_date_range')
        ft = frame.on_or_after(self.min_date)
        ft &= frame.before(self.max_date)
        query.push_filter(ft)
        query.execute()
        if not self.bs.periods.list_all():
            self.bs.periods.fetch(1)


class DatePagesCreator:
    def __init__(self, bs: LocalBase, min_date: dateclass, max_date: dateclass):
        self.bs = bs
        self.target = self.bs.dates
        self.min_date = min_date
        self.max_date = max_date

    def execute(self):
        for date in self.range_date():
            title = self.encode_title(date)
            if self.target.by_title[title]:
                continue
            tar = self.target.create_page()
            tar.props.write_title_at('index_as_target')

    def range_date(self):
        date = self.min_date
        while date < self.max_date:
            yield date
            date += timedelta(days=1)

    @staticmethod
    def encode_title(date: dateclass):
        date_handler = DateHandler(date)
        title = date_handler.strf_dig6_and_weekday()
        return title

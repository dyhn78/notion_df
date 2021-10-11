from __future__ import annotations

from notion_py.interface import RootEditor
from ..database_info import DatabaseInfo
from .common.match_algorithms import TernaryMatchAlgorithm, MonoMatchAlgorithm
from .common.date_index import DatePageProcessor, PeriodPageProcessor
from .common.query_maker import QueryMaker
from .frame import MatchFrames


class PropertyMatcher:
    def __init__(self, date_range=0):
        self.root = RootEditor()
        self.date_range = date_range
        self.query_maker = QueryMaker(self.date_range)

        self.periods = self.root.open_pagelist(*DatabaseInfo.PERIODS,
                                               frame=MatchFrames.PERIODS)
        self.dates = self.root.open_pagelist(*DatabaseInfo.DATES, frame=MatchFrames.DATES)
        self.journals = self.root.open_pagelist(*DatabaseInfo.JOURNALS,
                                                frame=MatchFrames.JOURNALS)
        self.memos = self.root.open_pagelist(*DatabaseInfo.MEMOS, frame=MatchFrames.MEMOS)
        self.writings = self.root.open_pagelist(*DatabaseInfo.WRITINGS,
                                                frame=MatchFrames.WRITINGS)

    def execute(self):
        self.make_query()

        self.match_to_itself()
        self.match_to_dates()
        self.match_to_periods()
        self.match_to_projects()

        self.apply_results()

    def make_query(self):
        for pagelist in [self.periods, self.dates, self.journals]:
            self.query_maker.query_as_parents(pagelist, 'index_as_domain')
        for pagelist in [self.memos, self.writings]:
            self.query_maker.query_as_parents(pagelist, 'index_as_domain')

    def apply_results(self):
        for pagelist in [self.periods, self.dates, self.journals, self.memos,
                         self.writings]:
            pagelist.execute()

    def match_to_itself(self):
        for pagelist in [self.journals, self.memos, self.writings]:
            MonoMatchAlgorithm(pagelist).to_itself('to_itself')

    def match_to_dates(self):
        for pagelist in [self.journals]:
            algorithm = TernaryMatchAlgorithm(pagelist, self.dates, pagelist)
            algorithm.by_ref('to_dates', 'up_self', 'to_dates')
            algorithm.by_index_then_create('to_dates', DatePageProcessor.get_title)
        for pagelist in [self.memos, self.writings]:
            algorithm = TernaryMatchAlgorithm(pagelist, self.dates, self.journals)
            algorithm.by_ref('to_dates', 'to_journals', 'to_dates')
            algorithm.by_index_then_create('to_dates', DatePageProcessor.get_title)

    def match_to_periods(self):
        TernaryMatchAlgorithm(self.dates, self.periods).by_index_then_create(
            'to_periods', PeriodPageProcessor.get_title,
            tar_writer_func=PeriodPageProcessor.writer(
                'manual_date_range'))
        for pagelist in [self.journals, self.memos, self.writings]:
            algorithm = TernaryMatchAlgorithm(pagelist, self.periods, self.dates)
            algorithm.by_ref('to_periods', 'to_dates', 'to_periods')

    def match_to_projects(self):
        algorithm = TernaryMatchAlgorithm(self.writings, None, self.journals)
        for to_project in ['to_themes', 'to_readings', 'to_channels']:
            algorithm.multi_by_ref(to_project, 'to_journals', to_project)

        # algorithm = TernaryMatchAlgorithm(self.journals, None, self.dates)
        # algorithm.by_ref('to_themes', 'to_dates', 'to_themes')

from __future__ import annotations

from .algorithm import TernaryMatchAlgorithm, MonoMatchAlgorithm
from .datetime import DatePageProcessor, PeriodPageProcessor
from .prop_frame import Frames
from .query_maker import QueryMaker
from ..page_ids import DatabaseInfo
from ...interface import RootEditor


class PropertyMatcher:
    def __init__(self, date_range=0):
        self.root = RootEditor()
        self.date_range = date_range
        self.query_maker = QueryMaker(self.date_range)

        self.periods = self.root.open_pagelist(*DatabaseInfo.PERIODS,
                                               frame=Frames.PERIODS)
        self.dates = self.root.open_pagelist(*DatabaseInfo.DATES, frame=Frames.DATES)
        self.journals = self.root.open_pagelist(*DatabaseInfo.JOURNALS,
                                                frame=Frames.JOURNALS)
        self.memos = self.root.open_pagelist(*DatabaseInfo.MEMOS, frame=Frames.MEMOS)
        self.shots = self.root.open_pagelist(*DatabaseInfo.SHOTS, frame=Frames.SHOTS)
        self.writings = self.root.open_pagelist(*DatabaseInfo.WRITINGS,
                                                frame=Frames.WRITINGS)

    def execute(self):
        self.make_query()

        self.match_to_itself()
        self.match_to_dates()
        self.match_to_periods()
        self.match_to_projects()

        self.apply_results()

    def make_query(self):
        for pagelist in [self.periods, self.dates, self.journals, self.shots]:
            self.query_maker.query_as_parents(pagelist, 'index_as_domain')
        for pagelist in [self.memos, self.writings]:
            self.query_maker.query_as_children(pagelist, 'index_as_domain', 'to_periods')
        for pagelist in [self.periods, self.dates, self.journals, self.memos, self.shots,
                         self.writings]:
            pagelist.set_overwrite_option(True)

    def apply_results(self):
        for pagelist in [self.periods, self.dates, self.journals, self.memos, self.shots,
                         self.writings]:
            pagelist.execute()

    def match_to_itself(self):
        for pagelist in [self.journals, self.shots, self.memos, self.writings]:
            MonoMatchAlgorithm(pagelist).to_itself('self_ref')

    def match_to_dates(self):
        TernaryMatchAlgorithm(self.journals, self.dates).by_index_then_create(
            'to_dates', DatePageProcessor.get_title)
        for pagelist in [self.shots, self.memos, self.writings]:
            TernaryMatchAlgorithm(pagelist, self.dates,
                                  self.journals).by_ref_then_index_then_create(
                'to_dates', 'to_journals', 'to_dates',
                DatePageProcessor.get_title)

    def match_to_periods(self):
        TernaryMatchAlgorithm(self.dates, self.periods).by_index_then_create(
            'to_periods', PeriodPageProcessor.get_title,
            tar_writer_func=PeriodPageProcessor.writer(
                'manual_date_range'))
        for pagelist in [self.journals, self.shots, self.memos, self.writings]:
            TernaryMatchAlgorithm(pagelist, self.periods, self.dates).by_ref(
                'to_periods', 'to_dates', 'to_periods')

    def match_to_projects(self):
        alg = TernaryMatchAlgorithm(self.writings, None, self.shots)
        for to_project in ['to_themes', 'to_readings', 'to_channels']:
            alg.multi_by_ref(to_project, 'to_shots', to_project)

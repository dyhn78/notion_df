from abc import ABCMeta

from notion_zap.cli.struct import DateValue
from ..common.base import Matcher
from ..common.date_index import DateHandler
from ..common.helpers import (
    overwrite_prop,
    fetch_unique_page_from_relation,
    query_target_by_idx
)


class PeriodMatcherAbs(Matcher, metaclass=ABCMeta):
    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.periods
        self.to_tar = 'to_periods'
        self.tars_by_index = self.target.by_idx_value_at('index_as_target')

    def match_period_by_idx(self, date_handler: DateHandler):
        tar_idx = date_handler.strf_year_and_week()
        if tar := self.tars_by_index.get(tar_idx):
            return tar
        if tar := query_target_by_idx(self.target, tar_idx, 'text'):
            self.tars_by_index.update({tar_idx: tar})
            return tar
        return self.create_period_by_idx(date_handler, tar_idx)

    def create_period_by_idx(self, date_handler: DateHandler, tar_idx):
        tar = self.target.create_page()
        tar.props.write_title_at('index_as_target', tar_idx)
        self.tars_by_index.update({tar_idx: tar})
        date_range = DateValue(
            start_date=date_handler.first_day_of_week(),
            end_date=date_handler.last_day_of_week()
        )
        tar.props.write_date_at('manual_date_range', date_range)
        tar.save()
        return tar


class PeriodMatcherType1(PeriodMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [self.bs.dates]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if dom.props.read_at(self.to_tar):
                    continue
                tar_id = self.determine_tar_id(dom)
                overwrite_prop(dom, self.to_tar, tar_id)

    def determine_tar_id(self, dom):
        tar = self.determine_tar(dom)
        return tar.block_id

    def determine_tar(self, dom):
        dom_idx: DateValue = dom.props.read_at('index_as_domain')
        date_handler = DateHandler(dom_idx.start)
        return self.match_period_by_idx(date_handler)


class PeriodMatcherType2(PeriodMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.dates
        self.to_ref = 'to_dates'
        self.domains = [
            self.bs.journals, self.bs.writings, self.bs.memos, self.bs.schedules,
            self.bs.readings
        ]

    def execute(self):
        for domain in self.domains:
            for dom in domain:
                if dom.props.read_at(self.to_tar):
                    continue
                if tar_id := self.determine_tar_id(dom):
                    overwrite_prop(dom, self.to_tar, tar_id)

    def determine_tar_id(self, dom):
        if ref := fetch_unique_page_from_relation(dom, self.reference, self.to_ref):
            if tar := fetch_unique_page_from_relation(ref, self.target, self.to_tar):
                return tar.block_id
        return ''
        # if tar_id := find_unique_target_id_by_ref(
        #         dom, self.reference, self.target, self.to_ref, self.to_tar):
        #     return tar_id
        # return ''
        # tar = self.determine_tar(dom)
        # return tar.block_id
        # message = f"Failed to connect <{dom.block_name}> to targets :: " \
        #           f"{self.tars_by_index}"
        # raise AssertionError(message)

    # def determine_tar(self, dom):
    #     dom_idx: DateValue = dom.props.read_at('index_as_domain')
    #     date_handler = DateHandler(dom_idx.start, add_timedelta=-5)
    #     return self.match_period_by_idx(date_handler)

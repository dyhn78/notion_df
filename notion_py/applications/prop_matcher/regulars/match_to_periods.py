from abc import ABCMeta

from ..common.date_index import PeriodPageProcessor
from ..common.helpers import overwrite_prop
from .helpers import create_unique_tar_by_idx, query_target_by_idx, \
    find_unique_target_id_by_ref
from .base import Matcher


class PeriodMatcherAbs(Matcher, metaclass=ABCMeta):
    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.periods
        self.to_tar = 'to_periods'
        self.tars_by_index = self.target.by_idx_value_at('index_as_target')
        self.idx_parser = PeriodPageProcessor.get_title


class PeriodMatcherType1(PeriodMatcherAbs):
    def execute(self):
        domain = self.bs.dates
        for dom in domain:
            if bool(dom.props.read_at(self.to_tar)):
                continue
            tar_id = self.determine_tar_id(dom)
            overwrite_prop(dom, self.to_tar, tar_id)

    def determine_tar_id(self, dom):
        tar = self.determine_tar(dom)
        return tar.master_id

    def determine_tar(self, dom):
        dom_idx = dom.props.read_at('index_as_domain')
        tar_idx = self.idx_parser(dom_idx)
        if tar := self.tars_by_index.get(tar_idx):
            return tar
        if tar := query_target_by_idx(self.target, tar_idx, 'text'):
            self.tars_by_index.update({tar_idx: tar})
            return tar
        if True:
            tar = create_unique_tar_by_idx(self.target, tar_idx)
            self.tars_by_index.update({tar_idx: tar})
            date_range = PeriodPageProcessor.get_date_range(tar_idx)
            tar.props.write_date_at('manual_date_range', date_range)
            tar.execute()
            return tar


class PeriodMatcherType2(PeriodMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.dates
        self.to_ref = 'to_dates'

    def execute(self):
        for domain in [self.bs.journals, self.bs.memos, self.bs.writings]:
            for dom in domain:
                if bool(dom.props.read_at(self.to_tar)):
                    continue
                tar_id = self.determine_tar_id(dom)
                overwrite_prop(dom, self.to_tar, tar_id)

    def determine_tar_id(self, dom):
        if tar_id := find_unique_target_id_by_ref(
                dom, self.reference, self.target, self.to_ref, self.to_tar):
            return tar_id
        tar = self.determine_tar(dom)
        return tar.master_id

    def determine_tar(self, dom):
        dom_idx = dom.props.read_at('index_as_domain')
        tar_idx = self.idx_parser(dom_idx)
        if tar := self.tars_by_index.get(tar_idx):
            return tar
        if tar := query_target_by_idx(self.target, tar_idx, 'text'):
            self.tars_by_index.update({tar_idx: tar})
            return tar
        message = f"Failed to connect <{tar_idx}> to targets :: {self.tars_by_index}"
        raise AssertionError(message)

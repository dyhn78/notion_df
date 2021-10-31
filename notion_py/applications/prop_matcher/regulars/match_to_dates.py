from abc import ABCMeta

from .base import LocalBase, Matcher
from .helpers import create_unique_tar_by_idx, \
    find_unique_target_id_by_homo_ref, query_target_by_idx, find_unique_target_id_by_ref
from ..common.date_index import DatePageProcessor
from ..common.helpers import overwrite_prop


class DateMatcherAbs(Matcher, metaclass=ABCMeta):
    def __init__(self, bs: LocalBase):
        super().__init__(bs)
        self.target = self.bs.dates
        self.to_tar = 'to_dates'
        self.to_ref = 'to_journals'
        self.idx_parser = DatePageProcessor.get_title
        self.tars_by_index = self.bs.dates.by_idx_value_at('index_as_target')


class DateMatcherType1(DateMatcherAbs):
    def execute(self):
        for domain in [self.bs.journals]:
            for dom in domain:
                if bool(dom.props.read_at(self.to_tar)):
                    continue
                tar_id = self.determine_tar_id(dom, domain)
                overwrite_prop(dom, self.to_tar, tar_id)

    def determine_tar_id(self, dom, domain):
        if tar_id := find_unique_target_id_by_homo_ref(
                dom, domain, self.target, self.to_tar):
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
        if True:
            tar = create_unique_tar_by_idx(self.target, tar_idx)
            self.tars_by_index.update({tar_idx: tar})
            tar.save()
            return tar


class DateMatcherType2(DateMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.reference = self.bs.journals

    def execute(self):
        for domain in [self.bs.memos, self.bs.writings]:
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


class DateMatcherType3(DateMatcherAbs):
    def execute(self):
        pass
        # algorithm = TernaryMatchAlgorithm(self.journals, None, self.dates)
        # algorithm.by_ref('to_themes', 'to_dates', 'to_themes')

from abc import ABCMeta

from notion_py.interface.common import DateFormat
from ..common.base import Matcher
from ..common.date_index import ProcessTimeProperty
from ..common.helpers import overwrite_prop, find_unique_target_id_by_homo_ref, \
    find_unique_target_id_by_ref, query_target_by_idx


class DateMatcherAbs(Matcher, metaclass=ABCMeta):
    def __init__(self, bs):
        super().__init__(bs)
        self.target = self.bs.dates
        self.to_tar = 'to_dates'
        self.to_ref = 'to_journals'
        self.tars_by_index = self.bs.dates.by_idx_value_at('index_as_target')

    def match_date_by_idx(self, date_handler: ProcessTimeProperty):
        tar_idx = date_handler.strf_dig6_and_weekday()
        if tar := self.tars_by_index.get(tar_idx):
            return tar
        if tar := query_target_by_idx(self.target, tar_idx, 'text'):
            self.tars_by_index.update({tar_idx: tar})
            return tar
        return self.create_date_by_idx(tar_idx)

    def create_date_by_idx(self, tar_idx):
        tar = self.target.create_page_row()
        tar.props.write_at('index_as_target', tar_idx)
        self.tars_by_index.update({tar_idx: tar})
        tar.save()
        return tar


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
        date_handler = ProcessTimeProperty(dom_idx.start, add_timedelta=-5)
        return self.match_date_by_idx(date_handler)


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
        dom_idx: DateFormat = dom.props.read_at('index_as_domain')
        date_handler = ProcessTimeProperty(dom_idx.start, add_timedelta=-5)
        return self.match_date_by_idx(date_handler)


class DateMatcherType3(DateMatcherAbs):
    def execute(self):
        pass
        # algorithm = TernaryMatchAlgorithm(self.journals, None, self.dates)
        # algorithm.by_ref('to_themes', 'to_dates', 'to_themes')

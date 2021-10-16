from .struct import LocalBase, Matcher
from .helpers import find_unique_target_by_idx, create_unique_target_by_idx
from ..common.date_index import DatePageProcessor, PeriodPageProcessor
from ..common.helpers import overwrite_prop


class MatchertoDates(Matcher):
    def __init__(self, bs: LocalBase):
        super().__init__(bs)
        self.target = self.bs.dates
        self.to_tar = 'to_dates'
        self.to_ref = 'to_journals'
        self.idx_parser = DatePageProcessor.get_title
        self.tars_by_index = self.bs.dates.by_idx_value_at('index_as_target')

    def execute(self):
        self.type1()
        self.type2()
        self.type3()

    def type1(self):
        for domain in [self.bs.journals]:
            self.algs.uniquely_with_homo_ref_and_idx(
                domain, self.target, self.to_tar, self.idx_parser, self.tars_by_index)

    def type2(self):
        for domain in [self.bs.memos, self.bs.writings]:
            self.algs.uniquely_with_hetero_ref_and_idx(
                domain, self.bs.journals, self.bs.dates,
                self.to_ref, self.to_tar, self.idx_parser, self.tars_by_index)

    def type3(self):
        pass
        # algorithm = TernaryMatchAlgorithm(self.journals, None, self.dates)
        # algorithm.by_ref('to_themes', 'to_dates', 'to_themes')


class MatchertoPeriods(Matcher):
    def execute(self):
        self.match_dates_to_periods()
        self.match_others_to_periods()

    def match_dates_to_periods(self):
        domain = self.bs.dates
        target = self.bs.periods
        to_tar = 'to_periods'
        tars_by_index = target.by_idx_value_at('index_as_target')
        idx_parser = PeriodPageProcessor.get_title
        for dom in domain:
            if bool(dom.props.read_at(to_tar)):
                continue
            dom_idx = dom.props.read_at('index_as_domain')
            tar_idx = idx_parser(dom_idx)
            if tar := find_unique_target_by_idx(target, tar_idx, tars_by_index):
                pass
            else:
                tar = create_unique_target_by_idx(target, tar_idx)
                date_range = PeriodPageProcessor.get_date_range(tar_idx)
                tar.props.write_date_at('manual_date_range', date_range)
                tar.execute()
            tar_id = tar.master_id
            overwrite_prop(dom, to_tar, tar_id)

    def match_others_to_periods(self):
        target = self.bs.periods
        reference = self.bs.dates
        to_tar = 'to_periods'
        to_ref = 'to_dates'
        idx_parser = PeriodPageProcessor.get_title
        tars_by_index = self.bs.periods.by_idx_value_at('index_as_target')
        for domain in [self.bs.journals, self.bs.memos, self.bs.writings]:
            self.algs.uniquely_with_hetero_ref_and_idx(domain, reference, target,
                                                       to_ref,
                                                       to_tar, idx_parser,
                                                       tars_by_index)

import datetime as dt

from notion_zap.cli import editors
from notion_zap.cli.struct import DateFormat
from ..common.struct import Matcher
from ..common.helpers import extend_prop, fetch_all_pages_from_relation


class ProgressMatcherType1(Matcher):
    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.writings
        self.reference = self.bs.journals
        self.to_ref = 'to_journals'
        self.to_tars = ['to_themes', 'to_channels', 'to_readings']

    def execute(self):
        for dom in self.domain:
            for to_tar in self.to_tars:
                refs = fetch_all_pages_from_relation(
                    dom, self.reference, self.to_ref)
                tar_ids = []
                for ref in refs:
                    tar_ids.extend(ref.props.read_at(to_tar))
                extend_prop(dom, to_tar, tar_ids)


class ProgressMatcherType2(Matcher):
    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.dates
        self.reference = self.bs.journals
        self.to_ref = 'to_journals'
        self.to_tars = ['to_locations', 'to_channels']

    def execute(self):
        for dom in self.domain:
            for to_tar in self.to_tars:
                dom_date: DateFormat = dom.props.read_at('manual_date')
                if (not dom_date.start_date
                        or dom_date.start_date > dt.date.today()):
                    continue
                if tar_ids := self.determine_tar_ids(dom, to_tar):
                    extend_prop(dom, to_tar, tar_ids)
                if not dom.props.read_at('sync_status'):  # False
                    dom.props.write_checkbox_at('sync_status', True)

    def determine_tar_ids(self, dom: editors.PageRow, to_tar: str):
        refs = fetch_all_pages_from_relation(
            dom, self.reference, self.to_ref)
        tar_ids = []
        for ref in refs:
            tar_ids.extend(ref.props.read_at(to_tar))
        return tar_ids

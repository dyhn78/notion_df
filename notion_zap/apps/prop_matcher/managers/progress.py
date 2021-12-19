import datetime as dt
from typing import Optional

from notion_zap.cli import editors
from notion_zap.cli.structs import DateObject
from ..common.struct import EditorManager
from ..common.helpers import extend_prop, fetch_all_pages_of_relation, \
    fetch_unique_page_of_relation


class ProgressMatcherofWritingsDepr(EditorManager):
    Tdoms_ref1 = 'to_journals'
    Tdoms_ref2 = 'to_schedules'
    TL_tar = ['to_projects', 'to_channels', 'to_readings']

    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.writings
        self.reference1 = self.bs.journals
        self.reference2 = self.bs.schedules

    def execute(self):
        for dom in self.domain.rows:
            for T_tar in self.TL_tar:
                tar_ids = []
                ref1s = fetch_all_pages_of_relation(dom, self.reference1, self.Tdoms_ref1)
                for ref1 in ref1s:
                    tar_ids.extend(ref1.props.read_tag(T_tar))
                ref2s = fetch_all_pages_of_relation(dom, self.reference2, self.Tdoms_ref2)
                for ref2 in ref2s:
                    tar_ids.extend(ref2.props.read_tag(T_tar))
                extend_prop(dom, T_tar, tar_ids)


class ProgressMatcherofReadings(EditorManager):
    Tmedia_type = 'media_type'
    T_tar = 'to_channels'
    Lmedia_type_empty = 'empty'

    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.readings
        self.target = self.bs.channels

    def execute(self):
        for dom in self.domain.rows:
            self.match(dom)

    def match(self, dom: editors.PageRow) -> Optional[str]:
        if dom.props.read_tag(self.Tmedia_type):
            return
        tar = fetch_unique_page_of_relation(dom, self.target, self.T_tar)
        if tar_val := tar.props.read_tag(self.Tmedia_type):
            dom.props.write_select(tag=self.Tmedia_type, value=tar_val)
        else:
            dom.props.write_select(tag=self.Tmedia_type, label=self.Lmedia_type_empty)


# TODO : 전역 -> 전체 복사 기능
class ProgressMatcherofDatesDepr(EditorManager):
    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.dates
        self.reference = self.bs.journals
        self.to_ref = 'to_journals'
        self.to_tars = ['to_locations', 'to_channels']

    def execute(self):
        for dom in self.domain.rows:
            for to_tar in self.to_tars:
                dom_date: DateObject = dom.props.read_tag('manual_date')
                if (not dom_date.start_date
                        or dom_date.start_date > dt.date.today()):
                    continue
                if tar_ids := self.determine_tar_ids(dom, to_tar):
                    extend_prop(dom, to_tar, tar_ids)
                if not dom.props.read_tag('sync_status'):  # False
                    dom.props.write_checkbox(tag='sync_status', value=True)

    def determine_tar_ids(self, dom: editors.PageRow, to_tar: str):
        refs = fetch_all_pages_of_relation(dom, self.reference, self.to_ref)
        tar_ids = []
        for ref in refs:
            tar_ids.extend(ref.props.read_tag(to_tar))
        return tar_ids

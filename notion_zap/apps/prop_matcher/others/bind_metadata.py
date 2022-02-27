import datetime as dt

from notion_zap.cli.structs import DateObject
from notion_zap.apps.prop_matcher.struct import TableModuleDepr
from notion_zap.apps.prop_matcher.common import write_extendedly


# TODO
class ProgressMatcherofDates(TableModuleDepr):
    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.dates
        self.ref_zip = [
            (self.bs.checks, 'checks'),
        ]
        self.collect_zip = [
            (
                'projects_total',  # dom collector ('종합')
                ['projects'],  # dom setter ('직결')
                # list of (ref_tag, ref setter)
                [
                    ('checks', ['projects', 'projects_context']),
                    ('writings', ['projects', 'projects_context']),
                    ('journals', ['projects']),
                    ('tasks', ['projects']),
                ]
            ),
            (
                'domains_total',
                ['domains'],
                [
                    ('checks', ['domains_context']),
                    ('writings', ['domains']),
                    ('journals', ['domains']),
                    ('tasks', ['domains']),
                ]
            ),
            (
                'channels_total',
                ['channels'],
                [
                    ('checks', ['channels', 'channels_context']),
                    ('writings', ['channels']),
                    ('journals', ['channels']),
                    ('tasks', ['channels']),
                ]
            ),
            (
                'readings_total',
                ['readings_begin'],
                [
                    ('checks', ['readings', 'readings_context']),
                    ('writings', ['readings']),
                    ('journals', ['readings']),
                    ('tasks', ['readings']),
                ]
            ),
        ]

    def __call__(self):
        pass


class ProgressMatcherofDatesDepr(TableModuleDepr):
    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.dates
        self.reference = self.bs.checks
        self.to_ref = 'checks'
        self.to_tars = ['locations', 'channels']

    def __call__(self):
        for dom in self.domain.rows:
            for to_tar in self.to_tars:
                dom_date: DateObject = dom.read_tag('dateval_manual')
                if (not dom_date.start_date
                        or dom_date.start_date > dt.date.today()):
                    continue
                if tar_ids := self.determine_tar_ids(dom, to_tar):
                    write_extendedly(dom, to_tar, tar_ids)
                if not dom.read_tag('sync_status'):  # False
                    dom.write_checkbox(tag='sync_status', value=True)

    def determine_tar_ids(self, dom: editors.PageRow, to_tar: str):
        refs = fetch_all_pages_of_relation(dom, self.reference, self.to_ref)
        tar_ids = []
        for ref in refs:
            tar_ids.extend(ref.read_tag(to_tar))
        return tar_ids


class ProgressMatcherofWritingsDepr(TableModuleDepr):
    Tdoms_ref1 = 'checks'
    Tdoms_ref2 = 'journals'
    TL_tar = ['projects', 'channels', 'readings']

    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.writings
        self.reference1 = self.bs.checks
        self.reference2 = self.bs.journals

    def __call__(self):
        for dom in self.domain.rows:
            for T_tar in self.TL_tar:
                tar_ids = []
                ref1s = fetch_all_pages_of_relation(dom, self.reference1, self.Tdoms_ref1)
                for ref1 in ref1s:
                    tar_ids.extend(ref1.read_tag(T_tar))
                ref2s = fetch_all_pages_of_relation(dom, self.reference2, self.Tdoms_ref2)
                for ref2 in ref2s:
                    tar_ids.extend(ref2.read_tag(T_tar))
                write_extendedly(dom, T_tar, tar_ids)

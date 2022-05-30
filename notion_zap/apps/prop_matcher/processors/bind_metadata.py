# import datetime as dt
#
# from notion_zap.cli.structs import DatePropertyValue
# from notion_zap.apps.prop_matcher.struct import TableModuleDepr
# from notion_zap.apps.prop_matcher.common import write_extendedly
#
#
# class ProgressMatcherofDates(TableModuleDepr):
#     def __init__(self, root):
#         super().__init__(root)
#         self.domain = self.root.dates
#         self.ref_zip = [
#             (self.root.counts, 'counts'),
#         ]
#         self.collect_zip = [
#             (
#                 'projects_total',  # dom collector ('종합')
#                 ['processes'],  # dom setter ('직결')
#                 # list of (ref_tag, ref setter)
#                 [
#                     ('counts', ['processes', 'projects_context']),
#                     ('writings', ['processes', 'projects_context']),
#                     ('journals', ['processes']),
#                     ('tasks', ['processes']),
#                 ]
#             ),
#             (
#                 'domains_total',
#                 ['domains'],
#                 [
#                     ('counts', ['domains_context']),
#                     ('writings', ['domains']),
#                     ('journals', ['domains']),
#                     ('tasks', ['domains']),
#                 ]
#             ),
#             (
#                 'channels_total',
#                 ['channels'],
#                 [
#                     ('counts', ['channels', 'channels_context']),
#                     ('writings', ['channels']),
#                     ('journals', ['channels']),
#                     ('tasks', ['channels']),
#                 ]
#             ),
#             (
#                 'readings_total',
#                 ['readings_begin'],
#                 [
#                     ('counts', ['readings', 'readings_context']),
#                     ('writings', ['readings']),
#                     ('journals', ['readings']),
#                     ('tasks', ['readings']),
#                 ]
#             ),
#         ]
#
#     def __call__(self):
#         # pass
#
#
# class ProgressMatcherofDatesDepr(TableModuleDepr):
#     def __init__(self, root):
#         super().__init__(root)
#         self.domain = self.root.dates
#         self.reference = self.root.counts
#         self.to_ref = 'counts'
#         self.to_tars = ['locations', 'channels']
#
#     def __call__(self):
#         for dom in self.domain.rows:
#             for to_tar in self.to_tars:
#                 dom_date: DatePropertyValue = dom.read_key_alias('manual_date')
#                 if (not dom_date.start_date
#                         or dom_date.start_date > dt.date.today()):
#                     continue
#                 if tar_ids := self.determine_tar_ids(dom, to_tar):
#                     write_extendedly(dom, to_tar, tar_ids)
#                 if not dom.read_key_alias('sync_status'):  # False
#                     dom.write_checkbox(key_alias='sync_status', value=True)
#
#     def determine_tar_ids(self, dom: editors.PageRow, to_tar: str):
#         refs = fetch_all_pages_of_relation(dom, self.reference, self.to_ref)
#         tar_ids = []
#         for ref in refs:
#             tar_ids.extend(ref.read_key_alias(to_tar))
#         return tar_ids
#
#
# class ProgressMatcherofWritingsDepr(TableModuleDepr):
#     Tdoms_ref1 = 'counts'
#     Tdoms_ref2 = 'journals'
#     TL_tar = ['processes', 'channels', 'readings']
#
#     def __init__(self, root):
#         super().__init__(root)
#         self.domain = self.root.writings
#         self.reference1 = self.root.counts
#         self.reference2 = self.root.journals
#
#     def __call__(self):
#         for dom in self.domain.rows:
#             for T_tar in self.TL_tar:
#                 tar_ids = []
#                 ref1s = fetch_all_pages_of_relation(dom, self.reference1, self.Tdoms_ref1)
#                 for ref1 in ref1s:
#                     tar_ids.extend(ref1.read_key_alias(T_tar))
#                 ref2s = fetch_all_pages_of_relation(dom, self.reference2, self.Tdoms_ref2)
#                 for ref2 in ref2s:
#                     tar_ids.extend(ref2.read_key_alias(T_tar))
#                 write_extendedly(dom, T_tar, tar_ids)

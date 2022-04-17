# from __future__ import annotations
#
# from notion_zap.apps.prop_matcher.struct import MainEditorDepr
# from notion_zap.cli import editors
#
#
# class GcalMatchController:
#     def __init__(self, request_size=50):
#         self.root = GcalEditorBase(request_size)
#
#     def execute(self):
#         self.root.fetch()
#         agents: list[TableModuleDepr] = [
#             GcaltoScheduleMatcher(self.root),
#             GcalfromScheduleMatcher(self.root),
#         ]
#         for agent in agents:
#             agent()
#         self.root.save()
#
#
# class GcalEditorBase(MainEditorDepr):
#     def __init__(self, request_size: int):
#         super().__init__()
#         self.request_size = request_size
#         self.root.exclude_archived = True
#
#     def fetch(self):
#         self.fetch_one(self.journals)
#
#     def fetch_one(self, domain: editors.RowChildren):
#         query = domain.open_query()
#         maker = query.filter_manager_by_tags
#         ft = query.open_filter()
#         if domain is self.journals:
#             ft |= maker.relation('dates').is_empty()
#             ft |= maker.checkbox('gcal_sync_status').is_empty()
#             ft |= maker.text('gcal_link').is_empty()
#
#         query.push_filter(ft)
#         # query.preview()
#         query.execute()
#
#
# if __name__ == '__main__':
#     GcalMatchController(5).execute()

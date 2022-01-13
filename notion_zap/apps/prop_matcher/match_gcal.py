from __future__ import annotations

from notion_zap.apps.prop_matcher.modules import *
from notion_zap.apps.prop_matcher.common.struct import EditorBase
from notion_zap.cli import editors


class GcalMatchController:
    def __init__(self, request_size=50):
        self.bs = GcalEditorBase(request_size)

    def execute(self):
        self.bs.fetch()
        agents: list[TableModule] = [
            GcaltoScheduleMatcher(self.bs),
            GcalfromScheduleMatcher(self.bs),
        ]
        for agent in agents:
            agent()
        self.bs.save()


class GcalEditorBase(EditorBase):
    def __init__(self, request_size: int):
        super().__init__()
        self.request_size = request_size
        self.root.exclude_archived = True

    def fetch(self):
        self.fetch_one(self.schedules)

    def fetch_one(self, domain: editors.RowChildren):
        query = domain.open_query()
        maker = query.filter_manager_by_tags
        ft = query.open_filter()
        if domain is self.schedules:
            ft |= maker.relation('dates_deadline').is_empty()
            ft |= maker.checkbox('gcal_sync_status').is_empty()
            ft |= maker.text('gcal_link').is_empty()

        query.push_filter(ft)
        # query.preview()
        query.execute()


if __name__ == '__main__':
    GcalMatchController(5).execute()

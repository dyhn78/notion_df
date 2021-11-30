from __future__ import annotations

from notion_zap.apps.prop_matcher.managers import *
from notion_zap.apps.prop_matcher.common.struct import EditorManager, EditorBase
from notion_zap.cli import editors


class GcalMatchController:
    def __init__(self, request_size=50):
        self.bs = GcalEditorBase(request_size)

    def execute(self):
        self.bs.fetch()
        agents: list[EditorManager] = [
            GcaltoScheduleMatcher(self.bs),
            GcalfromScheduleMatcher(self.bs),
        ]
        for agent in agents:
            agent.execute()
        self.bs.save()


class GcalEditorBase(EditorBase):
    def __init__(self, request_size: int):
        super().__init__()
        self.request_size = request_size
        self.root.exclude_archived = True

    def fetch(self):
        self.fetch_one(self.schedules)

    def fetch_one(self, domain: editors.PageList):
        query = domain.open_query()
        maker = query.filter_maker
        ft = query.open_filter()
        if domain is self.schedules:
            ft |= maker.relation_at('to_scheduled_dates').is_empty()
            ft |= maker.checkbox_at('gcal_sync_status').is_empty()
            ft |= maker.text_at('gcal_link').is_empty()

        query.push_filter(ft)
        # query.preview()
        query.execute()


if __name__ == '__main__':
    GcalMatchController(5).execute()

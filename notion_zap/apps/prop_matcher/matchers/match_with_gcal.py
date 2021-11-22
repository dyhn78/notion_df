from abc import ABCMeta

from notion_zap.cli import editors
from ..common.struct import Matcher
from ..gcal.open_gcal import open_gcal


class GcalMatcherAbs(Matcher, metaclass=ABCMeta):
    def __init__(self, bs):
        super().__init__(bs)
        self.gcal = open_gcal()

    def write_gcal_event(self):
        self.gcal.events()


class GcalMatcherType1(GcalMatcherAbs):
    def __init__(self, bs):
        super().__init__(bs)
        self.domain = self.bs.schedules
        self.tag_gcal_status = 'gcal_status'
        self.tag_gcal_link = 'gcal_link'

    def execute(self):
        for dom in self.domain:
            if self.match(dom):
                pass

    def match(self, dom: editors.PageRow):
        if self.regard_as_done(dom):
            return None
        pass

    def regard_as_done(self, dom: editors.PageRow):
        return (
            dom.props.read_at(self.tag_gcal_status)
            and dom.props.read_at(self.tag_gcal_link)
        )



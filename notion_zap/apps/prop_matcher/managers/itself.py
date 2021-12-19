from ..common.struct import EditorManager


class SelfMatcher(EditorManager):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [
            self.bs.periods, self.bs.dates, self.bs.journals,
            self.bs.writings, self.bs.tasks, self.bs.schedules,
            self.bs.readings
        ]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if dom.read_tag('to_itself') != [dom.block_id]:
                    dom.write(tag='to_itself', value=dom.block_id)

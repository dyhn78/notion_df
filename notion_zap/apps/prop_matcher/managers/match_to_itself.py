from ..common.struct import EditorManager


class SelfMatcher(EditorManager):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [
            self.bs.periods, self.bs.dates, self.bs.journals,
            self.bs.writings, self.bs.memos, self.bs.schedules,
            self.bs.readings
        ]

    def execute(self):
        for domain in self.domains:
            for dom in domain.rows:
                if dom.props.read_tag('to_itself') != [dom.block_id]:
                    dom.props.write(tag='to_itself', value=dom.block_id)
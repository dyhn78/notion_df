from ..common.struct import RoutineManager


class SelfMatcher(RoutineManager):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [
            self.bs.periods, self.bs.dates, self.bs.journals,
            self.bs.writings, self.bs.memos, self.bs.schedules,
            self.bs.readings
        ]

    def execute(self):
        for domain in self.domains:
            for dom in domain.pages:
                if dom.props.read_at('to_itself') != [dom.block_id]:
                    dom.props.write_at('to_itself', [dom.block_id])

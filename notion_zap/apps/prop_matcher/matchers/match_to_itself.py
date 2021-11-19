from ..common.struct import Matcher


class SelfMatcher(Matcher):
    def execute(self):
        for pagelist in [
            self.bs.periods, self.bs.dates, self.bs.journals,
            self.bs.writings, self.bs.memos, self.bs.schedules,
            self.bs.readings
        ]:
            for dom in pagelist:
                if dom.props.read_at('to_itself'):
                    continue
                dom.props.write_at('to_itself', [dom.block_id])

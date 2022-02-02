from ..common.struct import TableModule


class SelfMatcher(TableModule):
    def __init__(self, bs):
        super().__init__(bs)
        self.domains = [
            self.bs.periods, self.bs.dates, self.bs.checks,
            self.bs.writings, self.bs.tasks, self.bs.journals,
            self.bs.readings
        ]

    def __call__(self):
        for domain in self.domains:
            for dom in domain.rows:
                if dom.read_tag('itself') != [dom.block_id]:
                    dom.write(tag='itself', value=dom.block_id)

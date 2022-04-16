from notion_zap.apps.prop_matcher.struct import Processor


class SelfProcessor(Processor):
    def __call__(self):
        for table in self.tables:
            for row in table.rows:
                if row.read_key_alias('itself') != [row.block_id]:
                    row.write(key_alias='itself', value=[row.block_id])

    @property
    def tables(self):
        return [
            self.bs.periods, self.bs.dates,
            self.bs.journals, self.bs.checks,
            self.bs.topics, self.bs.writings, self.bs.tasks,
            self.bs.readings,
        ]

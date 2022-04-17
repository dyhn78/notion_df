from notion_zap.apps.prop_matcher.struct import Processor


class SelfProcessor(Processor):
    def __call__(self):
        for key, table in self.bs.pick('itself'):
            for row in table.rows:
                if row.read_key_alias('itself') != [row.block_id]:
                    row.write(key_alias='itself', value=[row.block_id])

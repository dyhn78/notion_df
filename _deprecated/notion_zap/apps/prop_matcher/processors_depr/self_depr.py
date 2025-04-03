from notion_zap.apps.prop_matcher.match_struct import Processor


class SelfProcessorDepr(Processor):
    def __call__(self):
        for table in self.root.get_blocks(self.option.filter_key('itself')):
            for row in table.rows:
                if row.read_key_alias('itself') != [row.block_id]:
                    row.write(key_alias='itself', value=[row.block_id])

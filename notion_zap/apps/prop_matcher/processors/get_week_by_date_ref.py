from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.common import has_relation, GetterByReference, \
    set_relation, ReferenceInfo
from notion_zap.apps.prop_matcher.struct import Processor


class PeriodProcessorByDateRef(Processor):
    def __init__(self, root):
        super().__init__(root)

    def __call__(self):
        for table, tag_period, ref_info in self.iter_args():
            get_period = GetterByReference(self.root[MyBlock.weeks], ref_info)
            for row in table.rows:
                if has_relation(row, tag_period):
                    continue
                if period := get_period(row):
                    set_relation(row, period, tag_period)

    def iter_args(self):
        for key, table in self.bs.filtered_pick('weeks'):
            yield (table, 'dates',
                   ReferenceInfo(self.root[MyBlock.dates], 'dates', 'weeks'))

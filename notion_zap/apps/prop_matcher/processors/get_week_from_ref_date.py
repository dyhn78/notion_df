from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.struct import Processor
from notion_zap.apps.prop_matcher.utils.relation_prop_helpers import has_relation, \
    GetterByReference, \
    set_relation, ReferenceInfo


class WeekProcessorFromRefDate(Processor):
    def __init__(self, root, option):
        super().__init__(root, option)

    def __call__(self):
        for table, week_tag, ref_info in self.iter_args():
            get_period = GetterByReference(self.root[MyBlock.weeks], ref_info)
            for row in table.rows:
                if has_relation(row, week_tag):
                    continue
                if week_row := get_period(row):
                    set_relation(row, week_row, week_tag)

    def iter_args(self):
        for table in self.root.get_blocks(self.option.filter_pair('weeks')):
            yield (table, 'weeks',
                   ReferenceInfo(self.root[MyBlock.dates], 'dates', 'weeks'))

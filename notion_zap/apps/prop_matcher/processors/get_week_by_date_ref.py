from notion_zap.apps.prop_matcher.common import has_relation, ReferenceInfo, GetterByReference, \
    set_relation
from notion_zap.apps.prop_matcher.struct import Processor, MainEditorDepr


class PeriodProcessorByDateRef(Processor):
    def __init__(self, bs: MainEditorDepr):
        super().__init__(bs)

    def __call__(self):
        for table, tag_period, ref_info in self.args:
            get_period = GetterByReference(self.bs.periods, ref_info)
            for row in table.rows:
                if has_relation(row, tag_period):
                    continue
                if period := get_period(row):
                    set_relation(row, period, tag_period)

    @property
    def args(self):
        args = []
        for table in [
            self.bs.journals,
            self.bs.checks,
            self.bs.topics,
            self.bs.writings,
            self.bs.tasks,
            self.bs.readings,
        ]:
            args.append((
                table, 'periods',
                ReferenceInfo(self.bs.dates, 'dates', 'periods')
            ))
        # for table in [
        #     self.bs.journals, self.bs.checks,
        # ]:
        #     args.append((
        #         table, 'periods_created',
        #         ReferenceInfo(self.bs.dates, 'dates_created', 'periods')
        #     ))
        return args

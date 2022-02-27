from ..common import has_value, get_unique_page_from_relation
from ..struct import MainEditor


class BindSimpleProperties(MainEditor):
    def __init__(self, bs):
        super().__init__(bs)

    def __call__(self):
        for table, reference, tag_ref, tag_copy in self.args:
            for row in table.rows:
                if has_value(row, tag_copy):
                    continue
                if tar := get_unique_page_from_relation(row, reference, tag_ref):
                    if val_copy := tar.read_tag(tag_copy):
                        row.write_select(tag=tag_copy, value=val_copy)

    @property
    def args(self):
        return [(self.bs.readings, self.bs.channels, 'channels', 'media_type')]

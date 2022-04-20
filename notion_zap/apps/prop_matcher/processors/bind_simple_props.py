from notion_zap.apps.config import MyBlock as My
from notion_zap.apps.prop_matcher.struct import Processor
from notion_zap.apps.prop_matcher.utils.relation_prop_helpers import has_relation, \
    get_unique_page_from_relation


class BindSimpleProperties(Processor):
    def __init__(self, bs):
        super().__init__(bs)

    def __call__(self):
        for table, reference, tag_ref, tag_copy in self.args:
            for row in table.rows:
                if has_relation(row, tag_copy):
                    continue
                if tar := get_unique_page_from_relation(row, reference, tag_ref):
                    if val_copy := tar.read_key_alias(tag_copy):
                        row.write_select(key_alias=tag_copy, value=val_copy)

    @property
    def args(self):
        return [(self.root[My.readings], self.root[My.channels], 'channels', 'media_type')]

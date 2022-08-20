from notion_zap.apps.myblock import MyBlock as My
from notion_zap.apps.prop_matcher.struct import Processor
from notion_zap.apps.prop_matcher.utils.relation_prop_helpers import has_relation, \
    get_unique_page_from_relation


class PropertyProcessorByReference(Processor):
    def __init__(self, root, option):
        super().__init__(root, option)

    def __call__(self):
        for table, tag_copy, ref_tuples in self.args:
            for table_ref, tag_ref in ref_tuples:
                for row in table.rows:
                    if has_relation(row, tag_copy):
                        continue
                    if tar := get_unique_page_from_relation(row, table_ref, tag_ref):
                        if val_copy := tar.read_key_alias(tag_copy):
                            row.write_select(key_alias=tag_copy, value=val_copy)
                            continue
                    row.write_select(key_alias=tag_copy, value='👤직접 입력')

    @property
    def args(self):
        return [(self.root[My.readings], 'media_type', [(self.root[My.streams], 'streams')])]

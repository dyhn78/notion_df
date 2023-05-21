from uuid import UUID

from notion_df.entity import Namespace
from notion_df.object.filter import and_filter
from notion_df.property import DualRelationPropertyKey, PageProperties
from workflow.constant.block_enum import DatabaseEnum

# ['⚫️측면', '⚫️양상']
old_props_1 = [DualRelationPropertyKey(name) for name in ['⚫️주목', '⚫️지평']]
new_prop_1 = DualRelationPropertyKey('🟣관계')
old_prop_2 = DualRelationPropertyKey('⚫️측면')
new_prop_2 = DualRelationPropertyKey('🟣공통')
namespace = Namespace(print_body=False)
topics = database(DatabaseEnum.topics.id)


def main():
    while True:
        try:
            page = topics.query(and_filter([
                old_prop.filter.is_not_empty() for old_prop in (old_props_1 + [old_prop_2])]), page_size=1)[0]
        except IndexError:
            return

        print(page.properties.title.plain_text, page.url)
        new_page_properties = PageProperties()

        new_prop_1_value: set[UUID] = set()
        for old_prop in old_props_1:
            new_prop_1_value |= set(page.properties[old_prop])
            new_page_properties[old_prop] = new_prop_1.page_value()
        new_page_properties[new_prop_1] = new_prop_1.page_value(new_prop_1_value)

        new_page_properties[new_prop_2] = page.properties[old_prop_2]
        new_page_properties[old_prop_2] = new_prop_1.page_value()

        page.update(new_page_properties)


if __name__ == '__main__':
    main()

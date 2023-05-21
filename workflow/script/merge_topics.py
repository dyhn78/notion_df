from uuid import UUID

from notion_df.entity import Namespace, Database
from notion_df.object.filter import and_filter
from notion_df.property import DualRelationPropertyKey, PageProperties
from notion_df.variable import Settings
from workflow.constant.block_enum import DatabaseEnum

# ['⚫️측면', '⚫️양상']
old_props_1 = [DualRelationPropertyKey(name) for name in ['⚫️주목', '⚫️지평']]
new_prop_1 = DualRelationPropertyKey('🟣관계')
old_prop_2 = DualRelationPropertyKey('⚫️측면')
new_prop_2 = DualRelationPropertyKey('🟣공통')
namespace = Namespace(print_body=False)
topic_db = Database(DatabaseEnum.topic_db.id)


def main():
    while True:
        try:
            topic = topic_db.query(and_filter([
                old_prop.filter.is_not_empty() for old_prop in (old_props_1 + [old_prop_2])]), page_size=1)[0]
        except IndexError:
            return

        topic_new_properties = PageProperties()

        new_prop_1_value: set[UUID] = set()
        for old_prop in old_props_1:
            new_prop_1_value |= set(topic.properties[old_prop])
            topic_new_properties[old_prop] = new_prop_1.page_value()
        topic_new_properties[new_prop_1] = new_prop_1.page_value(new_prop_1_value)

        topic_new_properties[new_prop_2] = topic.properties[old_prop_2]
        topic_new_properties[old_prop_2] = new_prop_1.page_value()

        with Settings.print_body:
            topic.update(topic_new_properties)


if __name__ == '__main__':
    main()

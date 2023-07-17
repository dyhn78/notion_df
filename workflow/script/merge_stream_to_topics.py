from pprint import pprint

from notion_df.property import DualRelationProperty, PageProperties
from notion_df.variable import Settings
from workflow.main.block_enum import DatabaseEnum

topic_to_stream = DualRelationProperty('🔴진행')
topic_to_stream_old = DualRelationProperty('🔴depr')
topic_db = DatabaseEnum.subject_db.entity


def main():
    topics = topic_db.query(topic_to_stream_old.filter.is_not_empty())
    print(len(topics))
    print(sum(len(topic.properties[topic_to_stream]) for topic in topics))
    print(sum(len(topic.properties[topic_to_stream_old]) for topic in topics))
    pprint([(topic.properties.title.plain_text, topic.url) for topic in topics])
    with Settings.print:
        for topic in topics:
            topic_new_properties = PageProperties()
            topic_new_properties[topic_to_stream_old] = topic_to_stream_old.page_value()
            topic_new_properties[topic_to_stream] = topic_to_stream.page_value(
                set(topic.properties[topic_to_stream]) | set(topic.properties[topic_to_stream_old])
            )
            topic.update(topic_new_properties)


if __name__ == '__main__':
    main()

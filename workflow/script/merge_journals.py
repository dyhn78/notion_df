from pprint import pprint

from notion_df.object.property import DualRelationProperty, PageProperties
from notion_df.variable import Settings
from workflow.constant.block_enum import DatabaseEnum

journal_to_stream = DualRelationProperty('🔴전개')
journal_to_stream_old = DualRelationProperty('🔴depr')
journal_db = DatabaseEnum.journal_db.entity


def main():
    journals = journal_db.query(journal_to_stream_old.filter.is_not_empty())
    print(len(journals))
    print(sum(len(journal.properties[journal_to_stream]) for journal in journals))
    print(sum(len(journal.properties[journal_to_stream_old]) for journal in journals))
    pprint([(journal.properties.title.plain_text, journal.url) for journal in journals])
    for journal in journals:
        journal_new_properties = PageProperties()
        journal_new_properties[journal_to_stream_old] = journal_to_stream_old.page_value()
        journal_new_properties[journal_to_stream] = journal_to_stream.page_value(
            set(journal.properties[journal_to_stream]) | set(journal.properties[journal_to_stream_old])
        )
        with Settings.print:
            journal.update(journal_new_properties)


if __name__ == '__main__':
    main()

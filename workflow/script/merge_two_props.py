from pprint import pprint

from notion_df.property import DualRelationProperty, PageProperties
from notion_df.variable import Settings
from workflow.constant.block_enum import DatabaseEnum

issue_to_stream = DualRelationProperty('🔴진행')
issue_to_stream_old = DualRelationProperty('🔴관계')
issue_db = DatabaseEnum.issue_db.entity


def main():
    issues = issue_db.query(issue_to_stream_old.filter.is_not_empty())
    print(len(issues))
    print(sum(len(issue.properties[issue_to_stream]) for issue in issues))
    print(sum(len(issue.properties[issue_to_stream_old]) for issue in issues))
    # pprint([(issue.properties.title.plain_text, issue.url) for issue in issues])
    with Settings.print:
        for issue in issues:
            issue_new_properties = PageProperties()
            issue_new_properties[issue_to_stream_old] = issue_to_stream_old.page_value()
            issue_new_properties[issue_to_stream] = issue_to_stream.page_value(
                set(issue.properties[issue_to_stream]) | set(issue.properties[issue_to_stream_old])
            )
            issue.update(issue_new_properties)


if __name__ == '__main__':
    main()

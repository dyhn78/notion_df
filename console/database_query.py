from datetime import date
from pprint import pprint

from notion_df.entity import Namespace
from notion_df.object.common import DateRange
from notion_df.property import DatePropertyKey, URLPropertyKey

if __name__ == '__main__':
    namespace = Namespace()
    database = namespace.database(
        'https://www.notion.so/dyhn/961d1ca0a3d24a46b838ba85e710f18d?v=c88ba6af32e249c99aef15d7b8044bdf&pvs=4')
    my_date_equals_20230101 = DatePropertyKey('📆날짜').filter.equals(date(2023, 1, 1))
    response = database.query(my_date_equals_20230101, page_size=10)
    pprint(response)
    page_properties = response[0].properties
    url = page_properties[URLPropertyKey('url')]
    url2 = page_properties['url']
    daterange = page_properties[DatePropertyKey('date')]
    page_properties[DatePropertyKey('date')] = DateRange(date(2023, 1, 1), date(2023, 1, 2))
    # page_properties[DatePropertyKey('date')] = 2

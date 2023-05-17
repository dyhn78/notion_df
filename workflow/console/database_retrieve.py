from pprint import pprint

from notion_df.entity import Database, Namespace

# @pytest.fixture
# def database():
#     namespace = Namespace()
#     database: Database = namespace.database(
#         'https://www.notion.so/dyhn/d020b399cf5947a59d11a0b9e0ea45d0?v=b7bc6354436448c5ad285c89089f0a35&pvs=4')
#     return database
#
#
# def test_retrieve(database):
#     response = database.retrieve()
#     pprint(response)
#
#
# def test_property_type():
#     DateProperty('my-date').page()
#     TitleProperty('my-title').page()
#
#
# def test_filter(database):
#     my_date_equals_20230101 = DateProperty('my-date').filter.equals(datetime(2023, 1, 1))
#     database.query(my_date_equals_20230101, [])


if __name__ == '__main__':
    namespace = Namespace()
    database: Database = namespace.database(
        'https://www.notion.so/dyhn/961d1ca0a3d24a46b838ba85e710f18d?v=c88ba6af32e249c99aef15d7b8044bdf&pvs=4')
    response = database.retrieve()
    pprint(response)

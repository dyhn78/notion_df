from datetime import datetime
from pprint import pprint

import pytest
from notion_df.property_key import DatePropertyKey, TitlePropertyKey

from notion_df.entity import Database, Namespace


@pytest.fixture
def database():
    namespace = Namespace()
    database: Database = namespace.database(
        'https://www.notion.so/dyhn/d020b399cf5947a59d11a0b9e0ea45d0?v=b7bc6354436448c5ad285c89089f0a35&pvs=4')
    return database


def test_retrieve(database):
    response = database.retrieve()
    pprint(response)


def test_property_type():
    DatePropertyKey('my-date').page()
    TitlePropertyKey('my-title').page()


def test_filter(database):
    my_date_equals_20230101 = DatePropertyKey('my-date').filter.equals(datetime(2023, 1, 1))
    database.query(my_date_equals_20230101, [])

from datetime import datetime
from pprint import pprint

import pytest

from notion_df.entity import Database, Namespace
from notion_df.object.filter import PropertyFilter, RollupPropertyAggregateFilter
from notion_df.object.property import date_property_type


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
    date_property_type.page('name', 'date')


def test_filter(database):
    equals_20230101 = date_property_type.filter_type.equals(datetime(2023, 1, 1))
    property_filter = PropertyFilter('property_name', equals_20230101)
    rollup_property_aggregate_filter = RollupPropertyAggregateFilter('property_name_2', 'any', equals_20230101)
    database.query(property_filter & rollup_property_aggregate_filter, [])

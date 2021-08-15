from __future__ import annotations
from typing import Optional, Any

from page_deprecated import TabularPageDeprecated
from pagelist_deprecated import PageListDeprecated
from notion_py.gateway.query import Query


class PropertyFrame:
    def __init__(self, values=None):
        if type(values) == tuple:
            prop_name, prop_value = values
        elif type(values) == str:
            prop_name = values
            prop_value = None
        else:
            raise AssertionError(f'Invalid PropertyFrame: {values}')
        self.name = prop_name
        self.value = prop_value


class DataFrame:
    def __init__(self, database_id: str,
                 database_name: str,
                 properties: Optional[dict[str, Any]] = None,
                 unit=TabularPageDeprecated):
        self.database_id = database_id
        self.database_name = database_name
        self.props = {key: PropertyFrame(value) for key, value in properties.items()}
        self.unit = unit

    @staticmethod
    def _pagelist():
        return PageListDeprecated

    @classmethod
    def create_dummy(cls):
        return cls('', '')

    def execute_query(self, page_size=0) -> PageListDeprecated:
        query = self.make_query()
        return self.insert_query_deprecated(query, page_size=page_size)

    def make_query(self):
        return Query(self.database_id)

    def insert_query_deprecated(self, query: Query, page_size=0):
        response = query.execute()
        return self._pagelist()(response, self, self.unit)

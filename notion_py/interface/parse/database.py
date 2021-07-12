from collections import defaultdict
from pprint import pprint

from .page import PageProperty


class DatabaseProperty:
    def __init__(self, props_table: dict):
        self.props_table = props_table

    @classmethod
    def from_retrieve_response(cls, response: dict):
        """
        :argument response: notion.databases.retrieve(database_id: str) 메소드로 얻을 수 있다.
        """
        return cls(response['properties'])

    @property
    def prop_type_table(self) -> dict[str, str]:
        """
        :return {prop_name: prop_type for prop_name in database}
        """
        return {prop_name: rich_property_object['type']
                for prop_name, rich_property_object in self.props_table.items()}

    @property
    def prop_id_table(self) -> dict[str, str]:
        """
        :return {prop_name: prop_id for prop_name in database}
        """
        return {prop_name: rich_property_object['id']
                for prop_name, rich_property_object in self.props_table.items()}


class PagePropertyList:
    def __init__(self, database_id: str, page_parsers: list[PageProperty]):
        self.database_id = database_id
        self.parser_list = page_parsers
        self.search = PagePropertySearchAgent(self)

    @classmethod
    def from_query_response(cls, response: dict):
        database_id = 'None'
        return cls(database_id, [PageProperty.from_query_response(page_result, database_id)
                                 for page_result in response['results']])


class PagePropertySearchAgent:
    def __init__(self, caller):
        self.caller = caller
        self._page_parser_by_id = None
        self._id_by_unique_title = None
        self._id_by_index = defaultdict(dict)

    @property
    def page_parser_by_id(self) -> dict[dict]:
        if self._page_parser_by_id is None:
            self._page_parser_by_id = {page_object.page_id: page_object.props
                                       for page_object in self.caller.parser_list}
        return self._page_parser_by_id

    @property
    def id_by_unique_title(self) -> dict[dict]:
        if self._id_by_unique_title is None:
            self._id_by_unique_title = {page_object.title: page_object.page_id
                                        for page_object in self.caller.parser_list}
        return self._id_by_unique_title

    def id_by_index(self, prop_name) -> dict[dict]:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props[prop_name]: page_object.page_id
                       for page_object in self.caller.parser_list}
            except TypeError:
                try:
                    res = {page_object.props[prop_name][0]: page_object.page_id
                           for page_object in self.caller.parser_list}
                except TypeError:
                    page_object = self.caller.parser_list[0]
                    pprint(f"key : {page_object.props[prop_name]}")
                    pprint(f"value : {page_object.page_id}")
                    raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name]

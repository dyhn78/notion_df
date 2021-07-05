class DatabasePropertyParser:
    def __init__(self, retrieve_response: dict):
        """
        :argument retrieve_response: notion.databases.retrieve(database_id: str) 메소드로 얻을 수 있다.
        """
        self.results = retrieve_response
        self.properties_table = self.results['properties']

    @property
    def prop_type_table(self) -> dict[str, str]:
        """
        :return {prop_name: prop_type for prop_name in database}
        """
        return {prop_name: rich_property_object['type']
                for prop_name, rich_property_object in self.properties_table.items()}

    @property
    def prop_id_table(self) -> dict[str, str]:
        """
        :return {prop_name: prop_id for prop_name in database}
        """
        return {prop_name: rich_property_object['id']
                for prop_name, rich_property_object in self.properties_table.items()}


class PageListParser:
    def __init__(self, query_response: dict):
        self.has_more = query_response['has_more']
        self.next_cursor = query_response['next_cursor']
        self.list_of_objects = [QueryPageParser(page_result) for page_result in query_response['results']]
        self.__list_of_items = None
        self.__dict_by_id = None
        self.__title_to_id = None

    @property
    def list_of_items(self) -> list[dict]:
        if self.__list_of_items is None:
            self.__list_of_items = [{'id': page_object.id, 'properties': page_object.props}
                                    for page_object in self.list_of_objects]
        return self.__list_of_items

    @property
    def dict_by_id(self) -> dict[dict]:
        if self.__dict_by_id is None:
            self.__dict_by_id = {page_object.id: page_object.props for page_object in self.list_of_objects}
        return self.__dict_by_id

    @property
    def title_to_id(self) -> dict[dict]:
        if self.__title_to_id is None:
            self.__title_to_id = {page_object.title: page_object.id for page_object in self.list_of_objects}
        return self.__title_to_id

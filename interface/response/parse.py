class DatabaseParser:
    def __init__(self, retrieve_results: dict):
        """
        :argument retrieve_results: notion.databases.retrieve(database_id: str) 메소드로 얻을 수 있다.
        """
        self.results = retrieve_results
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
    def __init__(self, query_results: dict):
        self.has_more = query_results['has_more']
        self.next_cursor = query_results['next_cursor']
        self.list_of_objects = [PageParser(page_result) for page_result in query_results['results']]
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


class PageParser:
    # TODO: datetime.fromisoformat, isoformat 적용
    def __init__(self, page):
        self.id = page['id']
        self.title = None
        self.props = {prop_name: self.__flatten_rich_property(rich_property_object)
                      for prop_name, rich_property_object in page['properties'].items()}

    def __flatten_rich_property(self, rich_property_object):
        # print('>'*20)
        # pprint(rich_property_object)
        prop_type = rich_property_object['type']
        prop_object = rich_property_object[prop_type]

        if prop_type in ['title', 'rich_text', 'text']:
            plain_text = ''.join([rich_text_object['plain_text'] for rich_text_object in prop_object])
            rich_text = []
            for rich_text_object in prop_object:
                rich_text.append({key: rich_text_object[key]
                                  for key in ['type', 'text', 'mention', 'equation'] if key in rich_text_object})
            result = [plain_text, rich_text]
            if prop_type == 'title':
                self.title = result
        elif prop_type == 'select':
            result = prop_object['name']
        elif prop_type == 'multi_select':
            result = [select_object['name'] for select_object in prop_object]
            result.sort()
        elif prop_type in ['people', 'person']:
            result = []
            for select_object in prop_object:
                try:
                    res = select_object['name']
                except KeyError:
                    res = 'bot_' + select_object['id'][0:4]
                result.append(res)
            result.sort()
        elif prop_type == 'relation':
            result = [relation_object['id'] for relation_object in prop_object]
            result.sort()
        elif prop_type == 'rollup':
            # pprint(prop_object)
            value_type = prop_object['type']
            result = [self.__flatten_rich_property(rollup_object) for rollup_object in prop_object[value_type]]
            # print('\n')
            # pprint(result)
            result.sort()
        else:
            result = prop_object
        # print('<' * 20)
        # pprint(result)
        return result


class BlockParser:
    pass

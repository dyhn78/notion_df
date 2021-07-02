# from pprint import pprint


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


"""
plain_items의 반환값 예시:

    [{'back_relationX': ['e15c62be-b9e4-4bb5-9b62-9220804fe93f'],
      'checkboxX': False,
      'created_timeX': '2021-06-17T10:47:00.000Z',
      'fileX': [],
      'formulaX': {'number': 123, 'type': 'number'},
      'multi_selectX': [],
      'peopleX': [],
      'relationX': ['9ed7d4fe-3c29-4e66-a4ed-cfa450814653'],
      'rollupX': [[]],
      'rollupX2': [['1234 1647 ',
                    [{'text': {'content': '1234 ', 'link': None}, 'type': 'text'},
                     {'mention': {'page': {'id': 'e15c62be-b9e4-4bb5-9b62-9220804fe93f'},
                                  'type': 'page'},
                      'type': 'mention'},
                     {'text': {'content': ' ', 'link': None}, 'type': 'text'}]]],
      '속성': ['150 가나다 23610',
             [{'mention': {'page': {'id': 'a6a64f5c-0ed7-4127-a86b-72ac5b77c8db'},
                           'type': 'page'},
               'type': 'mention'},
              {'text': {'content': ' 가나다 ', 'link': None}, 'type': 'text'},
              {'mention': {'page': {'id': '3009f442-5e13-4828-9067-fbd574f31b49'},
                           'type': 'page'},
               'type': 'mention'}]],
      '이름': ['23610',
             [{'text': {'content': '23610', 'link': None}, 'type': 'text'}]]},
     {'back_relationX': ['3009f442-5e13-4828-9067-fbd574f31b49'],
      'checkboxX': False,
      'created_timeX': '2021-06-17T10:47:00.000Z',
      'fileX': [],
      'formulaX': {'number': 123, 'type': 'number'},
      'multi_selectX': [],
      'peopleX': [],
      'relationX': [],
      'rollupX': [],
      'rollupX2': [],
      '속성': ['1234 1647 ',
             [{'text': {'content': '1234 ', 'link': None}, 'type': 'text'},
              {'mention': {'page': {'id': 'e15c62be-b9e4-4bb5-9b62-9220804fe93f'},
                           'type': 'page'},
               'type': 'mention'},
              {'text': {'content': ' ', 'link': None}, 'type': 'text'}]],
      '이름': ['2580',
             [{'text': {'content': '2580', 'link': None}, 'type': 'text'}]]}]




plain_items의 입력값 예시:

    {'has_more': False,
     'next_cursor': None,
     'object': 'list',
     'results': [{'archived': False,
                  'created_time': '2021-06-14T06:56:58.744Z',
                  'id': '5720981f-aa3e-4632-846f-46f990b6779d',
                  'last_edited_time': '2021-06-16T06:34:00.000Z',
                  'object': 'page',
                  'parent': {'database_id': '5c021bea-3e29-41f3-9bff-902cb2ebfe47',
                             'type': 'database_id'},
                  'properties': {'Xmulti_select': {'id': '`f`<',
                                                   'multi_select': [{'color': 'purple',
                                                                     'id': '05bfb990-ff88-4a77-8d1b-168938008aaa',
                                                                     'name': 'a'}],
                                                   'type': 'multi_select'},
                                 'Xpeople': {'id': ':{tp',
                                             'people': [{'avatar_url': None,
                                                         'id': 'a007d150-bc67-422c-87db-030a71867dd9',
                                                         'name': 'Younghoon Yun',
                                                         'object': 'user',
                                                         'person': {'email': 'dyhn78@snu.ac.kr'},
                                                         'type': 'person'}],
                                             'type': 'people'},
                                 'Xselect': {'id': 'f[Wf',
                                             'select': {'color': 'green',
                                                        'id': '9780409b-7c94-4b4c-bbdb-27138e4f7222',
                                                        'name': '1'},
                                             'type': 'select'},
                                 'back_relationX': {'id': 'Nf[_',
                                                    'relation': [],
                                                    'type': 'relation'},
                                 'checkboxX': {'checkbox': False,
                                               'id': '_=tU',
                                               'type': 'checkbox'},
                                 'created_timeX': {'created_time': '2021-06-14T06:56:58.744Z',
                                                   'id': '`S?H',
                                                   'type': 'created_time'},
                                 'emailX': {'email': '123',
                                            'id': '^Hae',
                                            'type': 'email'},
                                 'fileX': {'files': [],
                                           'id': 'rphx',
                                           'type': 'files'},
                                 'formulaX': {'formula': {'number': 123,
                                                          'type': 'number'},
                                              'id': 'oTSh',
                                              'type': 'formula'},
                                 'relationX': {'id': 'CWgv',
                                               'relation': [{'id': '6ec57963-a8e6-4fb9-afa2-bf01ccc6dcf7'}],
                                               'type': 'relation'},
                                 'rollupX': {'id': 'nOH@',
                                             'rollup': {'array': [{'title': [{'annotations': {'bold': False,
                                                                                              'code': False,
                                                                                              'color': 'default',
                                                                                              'italic': False,
                                                                                              'strikethrough': False,
                                                                                              'underline': False},
                                                                              'href': None,
                                                                              'plain_text': '2',
                                                                              'text': {'content': '2',
                                                                                       'link': None},
                                                                              'type': 'text'}],
                                                                   'type': 'title'}],
                                                        'type': 'array'},
                                             'type': 'rollup'},
                                 'telephoneX': {'id': 'QSB_',
                                                'phone_number': '123',
                                                'type': 'phone_number'},
                                 'urlX': {'id': 'UFxg',
                                          'type': 'url',
                                          'url': '123'},
                                 '열': {'date': {'end': None, 'start': '2021-06-14'},
                                       'id': 'sed<',
                                       'type': 'date'},
                                 '이름': {'id': 'title',
                                        'title': [{'annotations': {'bold': False,
                                                                   'code': False,
                                                                   'color': 'default',
                                                                   'italic': False,
                                                                   'strikethrough': False,
                                                                   'underline': False},
                                                   'href': None,
                                                   'plain_text': '1',
                                                   'text': {'content': '1',
                                                            'link': None},
                                                   'type': 'text'}],
                                        'type': 'title'}}}]}
"""
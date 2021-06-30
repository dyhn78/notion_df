from pprint import pprint

class DatabaseRetrieveReader:
    def __init__(self, retrieve_results: dict):
        """
        :argument retrieve_results: notion.databases.retrieve(database_id: str) 메소드로 얻을 수 있다.
        """
        self.raw = retrieve_results

    @property
    def database_frame(self) -> dict[str, str]:
        """
        :return {prop_name: prop_type for prop_name in database}
        """
        decorated_properties = self.raw['properties']
        result = {}
        for prop_name, decorated_value in decorated_properties.items():
            result[prop_name] = decorated_value['type']
        return result


class DatabaseQueryReader:
    def __init__(self, query_results: dict):
        self.query_results = query_results

    @property
    def plain_items(self) -> list[dict]:
        decorated_pages = [pages['properties'] for pages in self.query_results['results']]
        result = []
        for decorated_page in decorated_pages:
            res = {}
            for key, decorated_property in decorated_page.items():
                # if key == 'rollupX': print(decorated_property)
                res[key] = self.__get_plain_value(decorated_property)
            result.append(res)
        return result

    # TODO: datetime.fromisoformat, isoformat 적용
    @classmethod
    def __get_plain_value(cls, rich_property_object):
        # print('>'*20)
        # pprint(rich_property_object)
        prop_type = rich_property_object['type']
        prop_object = rich_property_object[prop_type]

        if prop_type in ['title', 'rich_text', 'text']:
            plain_text = ''.join([rich_text_object['plain_text'] for rich_text_object in prop_object])
            result = [plain_text, prop_object]
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
            result = [cls.__get_plain_value(rollup_object) for rollup_object in prop_object['array']]
            # print('\n')
            # pprint(result)
            result.sort()
        else:
            result = prop_object
        # print('<' * 20)
        # pprint(result)
        return result


"""
flatten_query의 반환값 예시:

    [{'back_relationX': [],
      'checkboxX': False,
      'created_timeX': '2021-06-14T06:56:58.744Z',
      'dateX': {'end': None, 'start': '2021-06-14'},
      'emailX': '123',
      'fileX': [],
      'formulaX': {'number': 123, 'type': 'number'},
      'multi_selectX': ['a'],
      'peopleX': ['Younghoon Yun'],
      'relationX': ['6ec57963-a8e6-4fb9-afa2-bf01ccc6dcf7',
                    '9e2efdc4-308c-4ec6-97df-765db284f128'],
      'rollupX': [['Younghoon Yun', 'bot_3f83'], ['Younghoon Yun', 'bot_3f83']],
      'rollupX2': [['Younghoon Yun', 'bot_3f83'], ['Younghoon Yun', 'bot_3f83']],
      'selectX': '1',
      'telephoneX': '123',
      'urlX': '123',
      '속성': [{'annotations': {'bold': False,
                              'code': False,
                              'color': 'default',
                              'italic': False,
                              'strikethrough': False,
                              'underline': False},
              'href': None,
              'plain_text': 'asd',
              'text': {'content': 'asd', 'link': None},
              'type': 'text'}],
      '이름': '1'}]

flatten_query의 입력값 예시:

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
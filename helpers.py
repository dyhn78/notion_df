from typing import List, Dict, Any
# from pprint import pprint


# TODO datetime.fromisoformat, isoformat 적용
def plain_value(decorated_property) -> Any:
    prop_type = decorated_property['type']
    decorated_value = decorated_property[prop_type]

    if prop_type == 'title':
        result = ''.join([deco_text['plain_text'] for deco_text in decorated_value])
    elif prop_type == 'select':
        result = decorated_value['name']
    elif prop_type == 'multi_select':
        result = [single_dicts['name'] for single_dicts in decorated_value]
        result.sort()
    elif prop_type in ['people', 'person']:
        result = []
        for single_dicts in decorated_value:
            try:
                res = single_dicts['name']
            except KeyError:
                res = 'bot'
            result.append(res)
        result.sort()
    elif prop_type == 'relation':
        result = [single_dicts['id'] for single_dicts in decorated_value]
        result.sort()
    elif prop_type == 'rollup':
        result = [plain_value(deco_dict) for deco_dict in decorated_value['array']]
        if len(result) == 1:
            result = result[0]
        result.sort()
    else:
        result = decorated_value
    return result


def flatten_query(query_results: Dict) -> List[Dict]:
    decorated_pages = [pages['properties'] for pages in query_results['results']]
    result = []
    for decorated_page in decorated_pages:
        res = {}
        for key, decorated_property in decorated_page.items():
            # if key == 'rollupX': print(decorated_property)
            res[key] = plain_value(decorated_property)
        result.append(res)
    return result


"""
flatten_query의 반환값 예시:

    [{'Xmulti_select': ['a'],
      'Xpeople': ['Younghoon Yun'],
      'Xselect': '1',
      'back_relationX': [],
      'checkboxX': False,
      'created_timeX': '2021-06-14T06:56:58.744Z',
      'emailX': '123',
      'fileX': [],
      'formulaX': {'number': 123, 'type': 'number'},
      'relationX': ['6ec57963-a8e6-4fb9-afa2-bf01ccc6dcf7'],
      'rollupX': ['2'],
      'telephoneX': '123',
      'urlX': '123',
      '열': {'end': None, 'start': '2021-06-14'},
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


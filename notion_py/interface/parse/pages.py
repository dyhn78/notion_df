from datetime import datetime as datetimeclass


class PageProperty:
    def __init__(self, page_id: str, parent_id: str,
                 parent_is_database: bool, title: str, props: dict):
        self.page_id = page_id
        self.parent_id = parent_id
        self.parent_is_database = parent_is_database
        self.title = title
        self.props = props

    @classmethod
    def from_query_response(cls, response_frag, parent_id):
        self = cls(
            page_id=response_frag['id'],
            parent_id=parent_id,
            parent_is_database=True,
            title='',
            props={}
        )
        for prop_name, rich_property_object in response_frag['properties'].items():
            self.props[prop_name] = self.__flatten(rich_property_object)
        return self

    @classmethod
    def from_retrieve_response(cls, response):
        parent_type = response['parent']['type']
        if parent_type == 'database_id':
            parent_id = response['parent']['database_id']
            parent_is_database = True
        elif parent_type == 'page_id':
            parent_id = response['parent']['page_id']
            parent_is_database = False
        else:
            raise AssertionError
        self = cls(
            page_id=response['id'],
            parent_id=parent_id,
            parent_is_database=parent_is_database,
            title='',
            props={}
        )
        for prop_name, rich_property_object in response['properties'].items():
            self.props[prop_name] = self.__flatten(rich_property_object)
        return self

    def __flatten(self, rich_property_object):
        prop_type = rich_property_object['type']
        prop_object = rich_property_object[prop_type]

        if prop_type in ['title', 'rich_text', 'text']:
            plain_text = ''.join([rich_text_object['plain_text']
                                  for rich_text_object in prop_object])
            rich_text = []
            for rich_text_object in prop_object:
                rich_text.append(
                    {key: rich_text_object[key]
                     for key in ['type', 'text', 'mention', 'equation']
                     if key in rich_text_object}
                )

            if prop_type == 'title':
                self.title = plain_text
            return [plain_text, rich_text]

        elif prop_type == 'select':
            return prop_object['name']

        elif prop_type == 'multi_select':
            result = [select_object['name'] for select_object in prop_object]
            return sorted(result)

        elif prop_type in ['people', 'person', 'created_by', 'last_edited_by']:
            result = []
            for select_object in prop_object:
                try:
                    res = select_object['name']
                except KeyError:
                    res = 'bot_' + select_object['id'][0:4]
                result.append(res)
            return sorted(result)

        elif prop_type == 'date':
            if type(prop_object) == dict:
                return {key: self.__from_datestring(value)
                        for key, value in prop_object.items()}
            else:
                return None

        elif prop_type in ['created_time', 'last_edited_time']:
            return {'start': self.__from_datestring(prop_object[:-1]),
                    'end': None}

        elif prop_type == 'formula':
            return self.__flatten(prop_object)

        elif prop_type == 'relation':
            result = [relation_object['id'] for relation_object in prop_object]
            return sorted(result)

        elif prop_type == 'rollup':
            value_type = prop_object['type']
            try:
                rollup_objects = prop_object[value_type]
            except KeyError:
                return None
            if value_type not in prop_object:
                result = []
            else:
                try:
                    result = [self.__flatten(rich_property_obj)
                              for rich_property_obj in rollup_objects]
                    try:
                        result.sort()
                    except TypeError:
                        pass
                        # result.sort(key=lambda x: x[sorted(x.keys())[0]])
                        # 딕셔너리의 키 목록 중 사전순으로 가장 앞에 오는 것으로써 정렬한다.
                except TypeError:
                    return prop_object[value_type]
        else:
            return prop_object

        return result

    @staticmethod
    def __from_datestring(datestring):
        if type(datestring) == str:
            return datetimeclass.fromisoformat(datestring)
        else:
            return None

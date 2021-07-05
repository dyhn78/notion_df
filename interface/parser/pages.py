class PagePropertyParser:
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


class BlockListParser:
    pass

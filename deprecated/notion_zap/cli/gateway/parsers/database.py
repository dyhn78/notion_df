from notion_zap.cli.utility import url_to_id


class DatabaseParser:
    def __init__(self, response: dict, database_id: str = ''):
        self.database_id = url_to_id(database_id)
        self.created_time = response['created_time']
        self.last_edited_time = response['last_edited_time']

        table = response['properties']
        # {prop_name: data_type for prop_name in _}
        self.data_types = {prop_name: rich_property_object['type']
                           for prop_name, rich_property_object in table.items()}
        # {prop_name: prop_id for prop_name in _}
        self.prop_ids = {prop_name: rich_property_object['id']
                         for prop_name, rich_property_object in table.items()}

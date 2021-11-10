class DatabaseParser:
    def __init__(self, response: dict, database_id: str = ''):
        self.database_id = database_id
        table = response['properties']
        # {prop_name: prop_type for prop_name in _}
        self.prop_types = {prop_name: rich_property_object['type']
                           for prop_name, rich_property_object in table.items()}
        # {prop_name: prop_id for prop_name in _}
        self.prop_ids = {prop_name: rich_property_object['id']
                         for prop_name, rich_property_object in table.items()}

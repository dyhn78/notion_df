class DatabaseParser:
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

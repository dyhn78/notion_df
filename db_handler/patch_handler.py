from db_handler.parser import DatabaseParser as DBParser


class PatchHandler:
    def __init__(self, page_id: str, database_parser=None):
        self.page_id = page_id
        self.patch_handler = []
        self.__types_table = None
        self.__id_table = None
        if database_parser is not None:
            self.add_db_retrieve(database_parser)

    def add_db_retrieve(self, database_parser: DBParser):
        self.__types_table = database_parser.prop_type_table
        self.__id_table = database_parser.prop_id_table

    @property
    def apply(self):
        return {
            'page_id': self.page_id,
            'properties': self.patch_handler
        }

    def __append(self, prop_type: str, prop_name: str, prop_value):
        self.patch_handler.append({
            prop_name: {
                prop_type: prop_value
            }
        })

    def append(self, prop_name: str, prop_value):
        if self.__types_table is None:
            raise AssertionError
        prop_type = self.__types_table[prop_name]
        self.__append(prop_type, prop_name, prop_value)

    def append_title(self, prop_name: str, prop_value):
        prop_type = 'title'
        self.__append(prop_type, prop_name, prop_value)

    def append_rich_text(self, prop_name: str, prop_value):
        prop_type = 'rich_text'
        self.__append(prop_type, prop_name, prop_value)

    def append_relation(self, prop_name: str, prop_value):
        prop_type = 'relation'
        self.__append(prop_type, prop_name, prop_value)

    def append_number(self, prop_name: str, prop_value):
        prop_type = 'number'
        self.__append(prop_type, prop_name, prop_value)

    def append_checkbox(self, prop_name: str, prop_value):
        prop_type = 'checkbox'
        self.__append(prop_type, prop_name, prop_value)

    def append_select(self, prop_name: str, prop_value):
        prop_type = 'select'
        self.__append(prop_type, prop_name, prop_value)

    def append_multi_select(self, prop_name: str, prop_value):
        prop_type = 'multi_select'
        self.__append(prop_type, prop_name, prop_value)

    def append_date(self, prop_name: str, prop_value):
        prop_type = 'date'
        self.__append(prop_type, prop_name, prop_value)

    def append_url(self, prop_name: str, prop_value):
        prop_type = 'url'
        self.__append(prop_type, prop_name, prop_value)

    def append_email(self, prop_name: str, prop_value):
        prop_type = 'email'
        self.__append(prop_type, prop_name, prop_value)

    def append_phone_number(self, prop_name: str, prop_value):
        prop_type = 'phone_number'
        self.__append(prop_type, prop_name, prop_value)

    def append_files(self, prop_name: str, prop_value):
        prop_type = 'files'
        self.__append(prop_type, prop_name, prop_value)

    def append_people(self, prop_name: str, prop_value):
        prop_type = 'people'
        self.__append(prop_type, prop_name, prop_value)


class RichTextMaker:
    pass


"""
properties: [{
      "In stock": {
        "checkbox": True,
      },
    },
    {
      "Details": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Some more text with "
            }
          },
          {
            "type": "text",
            "text": {
              "content": "some"
            },
            "annotations": {
              "italic": True
            }
          },
          {
            "type": "text",
            "text": {
              "content": " "
            }
          },
          {
            "type": "text",
            "text": {
              "content": "fun"
            },
            "annotations": {
              "bold": true
            }
          },
          {
            "type": "text",
            "text": {
              "content": " "
            }
          },
          {
            "type": "text",
            "text": {
              "content": "formatting"
            },
            "annotations": {
              "color": "pink"
            }
          }
        ]
      }
    }]
"""
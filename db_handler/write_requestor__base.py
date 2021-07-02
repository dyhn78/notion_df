from abc import abstractmethod, ABCMeta

from decorator import PropertyDecorator
from abstract_structures import Requestor, DicttypeStack, ListtypeStack
from db_handler.parser import DatabaseParser as DBParser


class PropertyValueDict(DicttypeStack):
    pass


class BlockChildrenList(ListtypeStack):
    pass


class PageWriteRequestor(Requestor, metaclass=ABCMeta):
    def __init__(self, notion):
        super().__init__(notion)
        self.props = DicttypeStack(PropertyValueDict)

    def __append(self, prop_type: str, prop_name: str, decorated_object: PropertyDecorator):
        self.props[prop_name] = {prop_type: decorated_object.apply}

    def append_title(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'title'
        self.__append(prop_type, prop_name, decorated_object)


class DatabaseWriteRequestor(PageWriteRequestor, metaclass=ABCMeta):
    def __init__(self, notion, database_parser=None):
        super().__init__(notion)
        self.__types_table = None
        self.__id_table = None
        if database_parser is not None:
            self.__add_db_retrieve(database_parser)

    def __add_db_retrieve(self, database_parser: DBParser):
        self.__types_table = database_parser.prop_type_table
        self.__id_table = database_parser.prop_id_table

    def append(self, prop_name: str, decorated_object: PropertyDecorator):
        if self.__types_table is None:
            raise AssertionError
        prop_type = self.__types_table[prop_name]
        self.__append(prop_type, prop_name, decorated_object)

    def append_rich_text(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'rich_text'
        self.__append(prop_type, prop_name, decorated_object)

    def append_relation(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'relation'
        self.__append(prop_type, prop_name, decorated_object)

    def append_number(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'number'
        self.__append(prop_type, prop_name, decorated_object)

    def append_checkbox(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'checkbox'
        self.__append(prop_type, prop_name, decorated_object)

    def append_select(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'select'
        self.__append(prop_type, prop_name, decorated_object)

    def append_multi_select(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'multi_select'
        self.__append(prop_type, prop_name, decorated_object)

    def append_date(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'date'
        self.__append(prop_type, prop_name, decorated_object)

    def append_url(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'url'
        self.__append(prop_type, prop_name, decorated_object)

    def append_email(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'email'
        self.__append(prop_type, prop_name, decorated_object)

    def append_phone_number(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'phone_number'
        self.__append(prop_type, prop_name, decorated_object)

    def append_files(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'files'
        self.__append(prop_type, prop_name, decorated_object)

    def append_people(self, prop_name: str, decorated_object: PropertyDecorator):
        prop_type = 'people'
        self.__append(prop_type, prop_name, decorated_object)


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
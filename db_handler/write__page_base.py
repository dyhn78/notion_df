from abc import abstractmethod

from db_handler.decorator import Decorator
from db_handler.handler_base import RequestHandler
from db_handler.parser import DatabaseParser as DBParser


class PageWriteHandler(RequestHandler):
    def __init__(self, database_parser=None):
        self.properties = {}
        self.__types_table = None
        self.__id_table = None
        if database_parser is not None:
            self.__add_db_retrieve(database_parser)

    def __add_db_retrieve(self, database_parser: DBParser):
        self.__types_table = database_parser.prop_type_table
        self.__id_table = database_parser.prop_id_table

    @property
    @abstractmethod
    def apply(self):
        pass

    def __append(self, prop_type: str, prop_name: str, decorated_object: Decorator):
        self.properties[prop_name] = {prop_type: decorated_object.apply}

    def append(self, prop_name: str, decorated_object: Decorator):
        if self.__types_table is None:
            raise AssertionError
        prop_type = self.__types_table[prop_name]
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_title(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'title'
        self.__append(prop_type, prop_name, decorated_object.apply)


class DatabaseWriteHandler(PageWriteHandler):
    @property
    @abstractmethod
    def apply(self):
        pass

    def append_rich_text(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'rich_text'
        self.__append(prop_type, prop_name, decorated_object)

    def append_relation(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'relation'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_number(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'number'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_checkbox(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'checkbox'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_select(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'select'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_multi_select(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'multi_select'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_date(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'date'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_url(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'url'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_email(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'email'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_phone_number(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'phone_number'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_files(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'files'
        self.__append(prop_type, prop_name, decorated_object.apply)

    def append_people(self, prop_name: str, decorated_object: Decorator):
        prop_type = 'people'
        self.__append(prop_type, prop_name, decorated_object.apply)


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
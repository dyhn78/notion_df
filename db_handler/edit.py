from abc import ABCMeta

from db_handler.decorate__abstract import Requestor
from db_handler.decorate__frame import PagePropertyStack, DatabasePropertyStack
from db_handler.parse import DatabaseParser as DBParser


class PageEditRequestor(Requestor, metaclass=ABCMeta):
    def __init__(self, notion):
        super().__init__(notion)
        self.props = PagePropertyStack()


class DatabaseEditRequestor(PageEditRequestor, metaclass=ABCMeta):
    def __init__(self, notion, database_parser=None):
        super().__init__(notion)
        self.props = DatabasePropertyStack()
        self.__types_table = None
        self.__id_table = None
        if database_parser is not None:
            self.__add_db_retrieve(database_parser)

    def __add_db_retrieve(self, database_parser: DBParser):
        self.__types_table = database_parser.prop_type_table
        self.__id_table = database_parser.prop_id_table


class PageUpdateRequestor(PageEditRequestor):
    def __init__(self, notion, page_id: str):
        super().__init__(notion)
        self.page_id = page_id

    @property
    def apply(self):
        return {
            'page_id': self.page_id,
            'properties': self.props
        }

    def execute(self):
        return self.notion.pages.edit(**self.apply)


class DatabaseUpdateRequestor(PageUpdateRequestor, DatabaseEditRequestor):
    def __init__(self, notion, page_id: str, database_parser=None):
        DatabaseEditRequestor.__init__(self, notion, database_parser)
        self.page_id = page_id


class PageCreateRequestor(PageEditRequestor):
    parent_id_type = 'page_id'

    def __init__(self, notion, parent_id: str):
        super().__init__(notion)
        self.parent_id = parent_id

    @property
    def apply(self):
        return {
            'parent': {self.parent_id_type: self.parent_id},
            'properties': self.props
        }

    def execute(self):
        return self.notion.pages.edit()


class DatabaseCreateRequestor(PageCreateRequestor, DatabaseEditRequestor):
    parent_id_type = 'database_id'

    def __init__(self, notion, parent_id: str, database_parser=None):
        DatabaseEditRequestor.__init__(self, notion, database_parser)
        self.parent_id = parent_id

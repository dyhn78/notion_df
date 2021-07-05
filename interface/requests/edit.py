from abc import ABCMeta

from interface.requests.structures import Requestor
from interface.requests.edit_property_frame import PagePropertyStack, DatabasePropertyStack, BlockChildrenStack
from interface.parser.databases import DatabasePropertyParser as DBParser


class PageEdit(Requestor, metaclass=ABCMeta):
    def __init__(self, notion):
        super().__init__(notion)
        self.props = PagePropertyStack()


class PageUpdate(PageEdit):
    def __init__(self, notion, page_id: str):
        super().__init__(notion)
        self.page_id = {'page_id': page_id}

    def apply(self):
        return self.merge_dict(self.page_id, self.props.apply())

    def execute(self):
        return self.notion.pages.update(**self.apply())


class PageCreate(PageEdit):
    def __init__(self, notion, parent_id: str):
        super().__init__(notion)
        self.parent_id = {'page_id': parent_id}
        self.children = BlockChildrenStack()

    def apply(self):
        return self.merge_dict(self.parent_id, self.props.apply(), self.children.apply())

    def execute(self):
        return self.notion.pages.create_and_append_to_liststash()


class DatabaseEdit(PageEdit, metaclass=ABCMeta):
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


class DatabaseUpdate(DatabaseEdit, PageUpdate):
    def __init__(self, notion, page_id: str, database_parser=None):
        super().__init__(notion, database_parser)
        self.page_id = {'page_id': page_id}


class DatabaseCreate(DatabaseEdit, PageCreate):
    def __init__(self, notion, parent_id: str, database_parser=None):
        super().__init__(notion, database_parser)
        self.parent_id = {'database_id': parent_id}

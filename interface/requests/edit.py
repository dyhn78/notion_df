from abc import ABCMeta

from interface.requests.requestor import Requestor, retry
from interface.requests.edit_arguments import PagePropertyStack, DatabasePropertyStack, BlockChildrenStack
from interface.parse.databases import DatabasePropertyParser as DBParser
from applications.helpers.page_id_to_url import page_id_to_url


class PageEdit(Requestor, metaclass=ABCMeta):
    def __init__(self):
        self.props = PagePropertyStack()


class PageUpdate(PageEdit):
    def __init__(self, page_id: str):
        super().__init__()
        self._page_id = {'page_id': page_id}

    def apply(self):
        return self._merge_dict(self._page_id, self.props.apply())

    @retry
    def execute(self):
        self.print_url()
        return self.notion.pages.update(**self.apply())

    def print_url(self):
        page_id = self._page_id['page_id']
        print(page_id_to_url(page_id))


class PageCreate(PageEdit):
    def __init__(self, parent_id: str):
        super().__init__()
        self._parent_id = {'page_id': parent_id}
        self.children = BlockChildrenStack()

    def apply(self):
        return self._merge_dict(self._parent_id, self.props.apply(), self.children.apply())

    @retry
    def execute(self):
        return self.notion.pages.create()


class DatabaseEdit(Requestor, metaclass=ABCMeta):
    def __init__(self, database_parser=None):
        self.props = DatabasePropertyStack()
        self.__types_table = None
        self.__id_table = None
        if database_parser is not None:
            self.__add_db_retrieve(database_parser)

    def __add_db_retrieve(self, database_parser: DBParser):
        self.__types_table = database_parser.prop_type_table
        self.__id_table = database_parser.prop_id_table


class DatabaseUpdate(DatabaseEdit, PageUpdate):
    def __init__(self, page_id: str, database_parser=None):
        DatabaseEdit.__init__(self, database_parser)
        self._page_id = {'page_id': page_id}


class DatabaseCreate(DatabaseEdit, PageCreate):
    def __init__(self, parent_id: str, database_parser=None):
        DatabaseEdit.__init__(self, database_parser)
        self._parent_id = {'database_id': parent_id}

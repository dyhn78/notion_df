from abc import ABCMeta

from interface.requests.requestor import Requestor, retry
from interface.requests.edit_arguments import PagePropertyStack, DatabasePropertyStack, BlockChildrenStack
from interface.parse.databases import DatabasePropertyParser as DBParser


class PageEdit(Requestor, metaclass=ABCMeta):
    def __init__(self):
        self.props = PagePropertyStack()


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


class PageUpdate(PageEdit):
    def __init__(self, page_id: str):
        super().__init__()
        self._id = page_id
        self._id_apply = {'page_id': self._id}

    def apply(self):
        return self._merge_dict(self._id_apply, self.props.apply())

    @retry
    def execute(self, print_info='page update'):
        if print_info:
            self.print_info(print_info)
        return self.notion.pages.update(**self.apply())


class PageCreate(PageEdit):
    def __init__(self, parent_id: str):
        super().__init__()
        self.children = BlockChildrenStack()
        self._id = parent_id
        self._id_apply = {'parent': {'page_id': self._id}}

    def apply(self):
        return self._merge_dict(self._id_apply, self.props.apply(), self.children.apply())

    @retry
    def execute(self, print_info=True):
        print('create..')
        return self.notion.pages.create(**self.apply())


class DatabaseUpdate(PageUpdate, DatabaseEdit):
    def __init__(self, page_id: str, database_parser=None):
        DatabaseEdit.__init__(self, database_parser)
        self._id = page_id
        self._id_apply = {'page_id': page_id}

    def execute(self, print_info='database update'):
        return PageUpdate.execute(self, print_info=print_info)


class DatabaseCreate(PageCreate, DatabaseEdit):
    def __init__(self, parent_id: str, database_parser=None):
        PageCreate.__init__(self, parent_id)
        DatabaseEdit.__init__(self, database_parser)
        self._id_apply = {'parent': {'database_id': self._id}}

    def execute(self, print_info=True):
        return PageCreate.execute(self, print_info=print_info)


class BlockAppend(Requestor):
    def __init__(self, block_id: str):
        self.children = BlockChildrenStack()
        self._id = block_id
        self._id_apply = {'block_id': self._id}

    def apply(self):
        return self._merge_dict(self._id_apply, self.children.apply())

    @retry
    def execute(self, print_info='block append'):
        if print_info:
            self.print_info(print_info)
        return self.notion.blocks.children.append(**self.apply())

from abc import ABCMeta

from .arguments import PagePropertyStack, DatabasePropertyStack, BlockChildrenStack
from notion_py.interface.structure import Requestor, retry
from notion_py.interface.parse import DatabaseProperty


class UpdateRequest(Requestor):
    def __init__(self, id_raw: str, id_apply: dict[str, str], props: PagePropertyStack):
        self._id_raw = id_raw
        self._id_apply = id_apply
        self.props = props

    def apply(self):
        return self._merge_dict(self._id_apply, self.props.apply())

    def __bool__(self):
        return bool(self.props.apply())

    @retry
    def execute(self, print_info='update..'):
        if not self:
            return {}
        if print_info:
            self.print_info(print_info)
        return self.notion.pages.update(**self.apply())

    @classmethod
    def under_page(cls, page_id):
        return cls(
            id_raw=page_id,
            id_apply={'page_id': page_id},
            props=PagePropertyStack()
        )


class CreateRequest(Requestor):
    def __init__(self, id_raw: str, id_apply: dict[str, dict], props: PagePropertyStack):
        self._id_raw = id_raw
        self._id_apply = id_apply
        self.props = props
        self.children = BlockChildrenStack()

    def apply(self):
        return self._merge_dict(self._id_apply, self.props.apply(), self.children.apply())

    def __bool__(self):
        return bool(self.props.apply()) and bool(self.children.apply())

    @retry
    def execute(self, print_info='create..'):
        if not self:
            return {}
        if print_info:
            print(print_info)
        return self.notion.pages.create(**self.apply())

    @classmethod
    def under_page(cls, parent_id: str):
        return cls(
            id_raw=parent_id,
            id_apply={'parent': {'page_id': parent_id}},
            props=PagePropertyStack()
        )


class DatabaseEdit(Requestor, metaclass=ABCMeta):
    def __init__(self, database_parser=None):
        self.id_table = None
        self.types_table = None
        if database_parser is not None:
            assert type(database_parser) == DatabaseProperty
            self.id_table = database_parser.prop_id_table
            self.types_table = database_parser.prop_type_table


class UpdateunderDatabase(UpdateRequest, DatabaseEdit):
    def __init__(self, page_id: str, database_parser=None):
        UpdateRequest.__init__(
            self,
            id_raw=page_id,
            id_apply={'page_id': page_id},
            props=DatabasePropertyStack()
        )
        DatabaseEdit.__init__(self, database_parser)


class CreateunderDatabase(CreateRequest, DatabaseEdit):
    def __init__(self, parent_id: str, database_parser=None):
        CreateRequest.__init__(
            self,
            id_raw=parent_id,
            id_apply={'parent': {'database_id': self._id_raw}},
            props=DatabasePropertyStack()
        )
        DatabaseEdit.__init__(self, database_parser)


class AppendBlock(Requestor):
    def __init__(self, block_id: str):
        self._id_raw = block_id
        self._id_apply = {'block_id': block_id}
        self.children = BlockChildrenStack()

    def apply(self):
        return self._merge_dict(self._id_apply, self.children.apply())

    def __bool__(self):
        return bool(self.children.apply())

    @retry
    def execute(self, print_info='append..'):
        if not self:
            return {}
        if print_info:
            self.print_info(print_info)
        return self.notion.blocks.children.append(**self.apply())

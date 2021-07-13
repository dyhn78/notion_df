from abc import ABCMeta

from notion_py.interface.structure import Requestor, retry, ignore_if_empty
from notion_py.interface.parse import DatabaseProperty
from .property_stack import BasicPagePropertyStack, TabularPagePropertyStack
from .block_stack import BlockChildrenStack
from .constants import DEFAULT_OVERWRITE, DEFAULT_EDIT_MODE


class UpdateBasicPage(Requestor):
    def __init__(self, page_id, overwrite=DEFAULT_OVERWRITE):
        self.page_id = page_id
        self._id_apply = {'page_id': page_id}
        self._overwrite = overwrite
        self.props = BasicPagePropertyStack(overwrite=self._overwrite)

    def apply(self):
        return self._merge_dict(self._id_apply, self.props.apply())

    def __bool__(self):
        return bool(self.props.apply())

    @retry
    @ignore_if_empty
    def execute(self, print_info='update..'):
        if print_info:
            self.print_info(print_info)
        res = self.notion.pages.update(**self.apply())
        self.props = BasicPagePropertyStack(overwrite=self._overwrite)
        return res


class CreateBasicPage(Requestor):
    def __init__(self, parent_id: str):
        self.page_id = parent_id
        self._id_apply = {'parent': {'page_id': parent_id}}
        self.props = BasicPagePropertyStack(overwrite=DEFAULT_OVERWRITE)
        self.children = BlockChildrenStack(edit_mode=DEFAULT_EDIT_MODE)

    def apply(self):
        return self._merge_dict(self._id_apply, self.props.apply(),
                                self.children.apply())

    def __bool__(self):
        return bool(self.props.apply()) and bool(self.children.apply())

    @retry
    @ignore_if_empty
    def execute(self, print_info='create..'):
        if print_info:
            print(print_info)
        res = self.notion.pages.create(**self.apply())
        self.props = BasicPagePropertyStack(overwrite=DEFAULT_OVERWRITE)
        self.children = BlockChildrenStack(edit_mode=DEFAULT_EDIT_MODE)
        return res


class DatabaseTable(metaclass=ABCMeta):
    def __init__(self, parsed_database: DatabaseProperty = None):
        self.id_table = None
        self.types_table = None
        if parsed_database is not None:
            self.id_table = parsed_database.prop_id_table
            self.types_table = parsed_database.prop_type_table


class UpdateTabularPage(UpdateBasicPage, DatabaseTable):
    def __init__(self, page_id: str, overwrite=DEFAULT_OVERWRITE,
                 parsed_database=None):
        UpdateBasicPage.__init__(self, page_id)
        DatabaseTable.__init__(self, parsed_database)
        self.props = TabularPagePropertyStack(overwrite=overwrite)


class CreateTabularPage(CreateBasicPage, DatabaseTable):
    def __init__(self, parent_id: str, parsed_database=None):
        CreateBasicPage.__init__(self, parent_id)
        DatabaseTable.__init__(self, parsed_database)
        self.props = TabularPagePropertyStack(overwrite=DEFAULT_OVERWRITE)


class AppendBlockChildren(Requestor):
    def __init__(self, parent_id: str, edit_mode=DEFAULT_EDIT_MODE):
        self._id_raw = parent_id
        self._id_apply = {'block_id': parent_id}
        self._edit_mode = edit_mode
        self.children = BlockChildrenStack(edit_mode=self._edit_mode)

    def apply(self):
        return self._merge_dict(self._id_apply, self.children.apply())

    def __bool__(self):
        return bool(self.children.apply())

    @retry
    @ignore_if_empty
    def execute(self, print_info='append..') -> dict:
        if print_info:
            self.print_info(print_info)
        res = self.notion.blocks.children.append(**self.apply())
        self.children = BlockChildrenStack(edit_mode=self._edit_mode)
        return res

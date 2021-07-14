from abc import ABCMeta

from notion_py.interface.structure import Requestor, retry, ignore_if_empty
from notion_py.interface.parse import DatabaseParser
from .property_stash import BasicPagePropertyStash, TabularPagePropertyStash
from .block_child_stash import BlockChildrenStash
from .block_contents import BlockContents


class UpdateBasicPage(Requestor):
    def __init__(self, page_id):
        self.page_id = page_id
        self._id_apply = {'page_id': page_id}
        self.props = BasicPagePropertyStash()

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
        self.props = BasicPagePropertyStash()
        return res


class CreateBasicPage(Requestor):
    def __init__(self, parent_id: str):
        self.page_id = parent_id
        self._id_apply = {'parent': {'page_id': parent_id}}
        self.props = BasicPagePropertyStash()
        self.children = BlockChildrenStash()

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
        self.props = BasicPagePropertyStash()
        self.children = BlockChildrenStash()
        return res


class DatabaseTable(metaclass=ABCMeta):
    def __init__(self, parsed_database: DatabaseParser = None):
        if parsed_database is not None:
            self.id_table = parsed_database.prop_id_table
            self.types_table = parsed_database.prop_type_table
        else:
            self.id_table = self.types_table = None


class UpdateTabularPage(UpdateBasicPage, DatabaseTable):
    def __init__(self, page_id: str, parsed_database: DatabaseParser = None):
        UpdateBasicPage.__init__(self, page_id)
        DatabaseTable.__init__(self, parsed_database)
        self.props = TabularPagePropertyStash()


class CreateTabularPage(CreateBasicPage, DatabaseTable):
    def __init__(self, parent_id: str, parsed_database: DatabaseParser = None):
        CreateBasicPage.__init__(self, parent_id)
        DatabaseTable.__init__(self, parsed_database)
        self.props = TabularPagePropertyStash()


class AppendBlockChildren(Requestor):
    def __init__(self, parent_id: str):
        self._id_raw = parent_id
        self._id_apply = {'block_id': parent_id}
        self.children = BlockChildrenStash()

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
        self.children = BlockChildrenStash()
        return res


class UpdateBlockContents(Requestor):
    # TODO : API가 만들어지면 추가할 예정.
    def __init__(self, block_id: str):
        self._id_raw = block_id
        self.contents = BlockContents()
        pass

    def apply(self):
        pass

    def execute(self):
        pass

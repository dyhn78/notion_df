from abc import ABCMeta

from notion_py.interface.utility import stopwatch, page_id_to_url
from ..parse_deprecated import DatabaseParser
from .block.stash import BlockChildrenStash
from .block.contents import BlockContents
from .property import BasicPagePropertyStash, TabularPagePropertyStash
from ...common import Gateway, retry_request


class UpdateBasicPage(Gateway):
    def __init__(self, page_id):
        self.page_id = page_id
        self._id_apply = {'page_id': page_id}
        self.props = BasicPagePropertyStash()

    def __bool__(self):
        return bool(self.props.unpack())

    def unpack(self):
        return dict(**self.props.unpack(),
                    page_id=self.page_id)

    @retry_request
    def execute(self):
        if not self.props:
            return {}
        res = self.notion.pages.update(**self.unpack())
        stopwatch(' '.join(['update', page_id_to_url(self.page_id)]))
        self.props = BasicPagePropertyStash()
        return res


class CreateBasicPage(Gateway):
    def __init__(self, parent_id: str):
        self.parent_id = parent_id
        self.props = BasicPagePropertyStash()
        self.children = BlockChildrenStash()

    def __bool__(self):
        return bool(self.props.unpack()) and bool(self.children.unpack())

    def unpack(self):
        return dict(**self.props.unpack(),
                    **self.children.unpack(),
                    parent={'page_id': self.parent_id})

    @retry_request
    def execute(self):
        if not (self.props or self.children):
            return {}
        res = self.notion.pages.create(**self.unpack())
        stopwatch(' '.join(['create', page_id_to_url(res['id'])]))
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


class AppendBlockChildren(Gateway):
    def __init__(self, parent_id: str):
        self.parent_id = parent_id
        self.children = BlockChildrenStash()

    def __bool__(self):
        return bool(self.children.unpack())

    def unpack(self):
        return dict(**self.children.unpack(),
                    block_id=self.parent_id)

    @retry_request
    def execute(self) -> dict:
        if not self.children:
            return {}
        stopwatch(' '.join(['append', page_id_to_url(self.parent_id)]))
        res = self.notion.blocks.children.append(**self.unpack())
        self.children = BlockChildrenStash()
        return res


class UpdateBlock(Gateway):
    # TODO : API가 만들어지면 추가할 예정.
    def __init__(self, block_id: str):
        self._id_raw = block_id
        self.contents = BlockContents()
        pass

    def __bool__(self):
        pass

    def unpack(self):
        pass

    def execute(self):
        pass

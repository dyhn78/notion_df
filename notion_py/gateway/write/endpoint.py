from abc import ABCMeta

from ...utility import stopwatch, page_id_to_url
from ..common import Requestor, retry_request
from ..parse import DatabaseParser
from .block.stash import BlockChildrenStash
from .block.contents import BlockContents
from .property import BasicPagePropertyStash, TabularPagePropertyStash


class UpdateBasicPage(Requestor):
    def __init__(self, page_id):
        self.page_id = page_id
        self._id_apply = {'page_id': page_id}
        self.props = BasicPagePropertyStash()

    def __bool__(self):
        return bool(self.props.apply())

    def apply(self):
        return dict(**self.props.apply(),
                    page_id=self.page_id)

    @retry_request
    def execute(self):
        if not self.props:
            return {}
        res = self.notion.pages.update(**self.apply())
        stopwatch(' '.join(['update', page_id_to_url(self.page_id)]))
        self.props = BasicPagePropertyStash()
        return res


class CreateBasicPage(Requestor):
    def __init__(self, parent_id: str):
        self.page_id = parent_id
        self.props = BasicPagePropertyStash()
        self.children = BlockChildrenStash()

    def __bool__(self):
        return bool(self.props.apply()) and bool(self.children.apply())

    def apply(self):
        return dict(**self.props.apply(),
                    **self.children.apply(),
                    parent={'page_id': self.page_id})

    @retry_request
    def execute(self):
        if not (self.props or self.children):
            return {}
        res = self.notion.pages.create(**self.apply())
        stopwatch(' '.join(['create', page_id_to_url(res['id'])]))
        self.props = BasicPagePropertyStash()
        self.children = BlockChildrenStash()
        return res


class UpdateTabularPage(UpdateBasicPage):
    def __init__(self, page_id: str):
        UpdateBasicPage.__init__(self, page_id)
        self.props = TabularPagePropertyStash()


class CreateTabularPage(CreateBasicPage):
    def __init__(self, parent_id: str):
        CreateBasicPage.__init__(self, parent_id)
        self.props = TabularPagePropertyStash()


class AppendBlockChildren(Requestor):
    def __init__(self, parent_id: str):
        self.parent_id = parent_id
        self.children = BlockChildrenStash()
        self.overwrite_option = True

    def __bool__(self):
        return bool(self.children.apply())

    def apply(self):
        return dict(**self.children.apply(),
                    block_id=self.parent_id)

    @retry_request
    def execute(self) -> dict:
        if not self.children:
            return {}
        stopwatch(' '.join(['append', page_id_to_url(self.parent_id)]))
        res = self.notion.blocks.children.append(**self.apply())
        self.children = BlockChildrenStash()
        return res


class UpdateBlock(Requestor):
    # TODO : API가 만들어지면 추가할 예정.
    def __init__(self, block_id: str):
        self._id_raw = block_id
        self.contents = BlockContents()
        pass

    def apply(self):
        pass

    def execute(self):
        pass

from .block import BlockChildrenStash, BlockContents
from .property import PagePropertyStash
from ...utility import stopwatch, page_id_to_url
from ..common import GatewayRequestor, retry_request


class UpdatePage(GatewayRequestor):
    def __init__(self, page_id):
        self.page_id = page_id
        self.props = PagePropertyStash()

    def __bool__(self):
        return bool(self.props.unpack())

    def unpack(self):
        return dict(**self.props.unpack(),
                    page_id=self.page_id)

    @retry_request
    def execute(self):
        if not bool(self):
            return {}
        res = self.notion.pages.update(**self.unpack())
        stopwatch(' '.join(['update', page_id_to_url(self.page_id)]))
        return res


class CreatePage(GatewayRequestor):
    def __init__(self, parent_id: str):
        self.parent_id = parent_id
        self.props = PagePropertyStash()
        self.children = BlockChildrenStash()

    def __bool__(self):
        return any([bool(self.props.unpack()),
                    bool(self.children.unpack())])

    def unpack(self):
        return dict(**self.props.unpack(),
                    **self.children.unpack(),
                    parent={'page_id': self.parent_id})

    @retry_request
    def execute(self):
        if not bool(self):
            return {}
        res = self.notion.pages.create(**self.unpack())
        stopwatch(' '.join(['create', page_id_to_url(res['id'])]))
        return res


class AppendBlockChildren(GatewayRequestor):
    def __init__(self, parent_id: str):
        self.parent_id = parent_id
        self.children = BlockChildrenStash()
        self.overwrite_option = True

    def __bool__(self):
        return bool(self.children.unpack())

    def unpack(self):
        return dict(**self.children.unpack(),
                    block_id=self.parent_id)

    @retry_request
    def execute(self):
        if not bool(self):
            return {}
        res = self.notion.blocks.children.append(**self.unpack())
        stopwatch(' '.join(['append', page_id_to_url(self.parent_id)]))
        return res


class UpdateBlock(GatewayRequestor):
    # TODO : API가 만들어지면 추가할 예정.
    def __init__(self, block_id: str):
        self.block_id = block_id
        self.contents = BlockContents()
        pass

    def __bool__(self):
        pass

    def unpack(self):
        pass

    def execute(self):
        pass

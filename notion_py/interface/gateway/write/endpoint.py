from .stash import BlockChildrenStash, PagePropertyStash, ArchiveToggle
from notion_py.interface.struct import Gateway, retry_request, drop_empty_request
from notion_py.interface.api_format.encode import BlockWriter
from ...utility import stopwatch, page_id_to_url


class CreatePage(Gateway, PagePropertyStash, BlockChildrenStash, ArchiveToggle):
    def __init__(self, parent_id: str, under_database: bool):
        PagePropertyStash.__init__(self)
        BlockChildrenStash.__init__(self)
        ArchiveToggle.__init__(self)
        self.parent_id = parent_id
        self.parent_type = 'database_id' if under_database else 'page_id'

    def __bool__(self):
        return any([PagePropertyStash.__bool__(self),
                    BlockChildrenStash.__bool__(self)])

    def clear(self):
        PagePropertyStash.clear(self)
        BlockChildrenStash.clear(self)

    def unpack(self):
        return dict(**PagePropertyStash.unpack(self),
                    **BlockChildrenStash.unpack(self),
                    **ArchiveToggle.unpack(self),
                    parent={self.parent_type: self.parent_id})

    @drop_empty_request
    @retry_request
    def execute(self) -> dict:
        res = self.notion.pages.create(**self.unpack())
        stopwatch(' '.join(['create', page_id_to_url(res['id'])]))
        self.clear()
        return res


class UpdatePage(Gateway, PagePropertyStash, ArchiveToggle):
    def __init__(self, page_id):
        PagePropertyStash.__init__(self)
        ArchiveToggle.__init__(self)
        self.page_id = page_id

    def __bool__(self):
        return PagePropertyStash.__bool__(self)

    def clear(self):
        PagePropertyStash.clear(self)

    def unpack(self):
        return dict(**PagePropertyStash.unpack(self),
                    **ArchiveToggle.unpack(self),
                    page_id=self.page_id)

    @drop_empty_request
    @retry_request
    def execute(self) -> dict:
        res = self.notion.pages.update(**self.unpack())
        stopwatch(' '.join(['update', page_id_to_url(self.page_id)]))
        self.clear()
        return res


class AppendBlockChildren(Gateway, BlockChildrenStash):
    def __init__(self, parent_id: str):
        BlockChildrenStash.__init__(self)
        self.parent_id = parent_id

    def __bool__(self):
        return BlockChildrenStash.__bool__(self)

    def clear(self):
        BlockChildrenStash.clear(self)

    def unpack(self):
        return dict(**BlockChildrenStash.unpack(self),
                    block_id=self.parent_id)

    @drop_empty_request
    @retry_request
    def execute(self) -> dict:
        res = self.notion.blocks.children.append_block(**self.unpack())
        stopwatch(' '.join(['append', page_id_to_url(self.parent_id)]))
        self.clear()
        return res


class UpdateBlock(Gateway):
    def __init__(self, block_id: str):
        self.block_id = block_id
        self._contents_value = None
        pass

    def __bool__(self):
        return self._contents_value is not None

    def clear(self):
        self._contents_value = None

    def apply_contents(self, carrier: BlockWriter):
        self._contents_value = carrier
        return carrier

    def unpack(self):
        return dict(**self._contents_value.unpack(),
                    block_id=self.block_id)

    @retry_request
    def execute(self) -> dict:
        """making a request with empty carrier
        will clear the original read_plain of block"""
        if self._contents_value is None:
            return {}
        res = self.notion.blocks.update(**self.unpack())
        stopwatch(' '.join(['update', page_id_to_url(self.block_id)]))
        self.clear()
        return res

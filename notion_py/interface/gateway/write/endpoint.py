from typing import Any

from .stash import BlockChildrenStash, PagePropertyStash, ArchiveToggle
from notion_py.interface.struct import Gateway, retry_request, drop_empty_request, \
    Editor
from notion_py.interface.api_encode import ContentsEncoder
from ...utility import stopwatch, page_id_to_url


class CreatePage(Gateway, PagePropertyStash, BlockChildrenStash, ArchiveToggle):
    def __init__(self, editor: Editor, under_database: bool):
        Gateway.__init__(self, editor)
        PagePropertyStash.__init__(self)
        BlockChildrenStash.__init__(self)
        ArchiveToggle.__init__(self)
        self.parent_type = 'database_id' if under_database else 'page_id'

    @property
    def target_id(self):
        return self.editor.parent_id

    def __bool__(self):
        return any([PagePropertyStash.__bool__(self),
                    BlockChildrenStash.__bool__(self)])

    def clear(self):
        PagePropertyStash.clear(self)
        BlockChildrenStash.clear(self)

    def unpack(self):
        res = dict(**PagePropertyStash.unpack(self),
                   **BlockChildrenStash.unpack(self),
                   parent={self.parent_type: self.target_id})
        if self._archive_value is not None:
            res.update(**ArchiveToggle.unpack(self))
        return res

    @drop_empty_request
    @retry_request
    def execute(self) -> dict:
        res = self.notion.pages.create(**self.unpack())
        stopwatch(' '.join(['create', page_id_to_url(res['id'])]))
        self.clear()
        return res


class UpdatePage(Gateway, PagePropertyStash, ArchiveToggle):
    def __init__(self, editor: Editor):
        Gateway.__init__(self, editor)
        PagePropertyStash.__init__(self)
        ArchiveToggle.__init__(self)

    def __bool__(self):
        return PagePropertyStash.__bool__(self)

    def clear(self):
        PagePropertyStash.clear(self)

    def unpack(self):
        res = dict(**PagePropertyStash.unpack(self),
                   page_id=self.target_id)
        if self._archive_value is not None:
            res.update(**ArchiveToggle.unpack(self))
        return res

    @drop_empty_request
    @retry_request
    def execute(self) -> dict:
        res = self.notion.pages.update(**self.unpack())
        stopwatch(' '.join(['update', page_id_to_url(self.target_id)]))
        self.clear()
        return res


class AppendBlockChildren(Gateway, BlockChildrenStash):
    def __init__(self, editor: Editor):
        Gateway.__init__(self, editor)
        BlockChildrenStash.__init__(self)

    def __bool__(self):
        return BlockChildrenStash.__bool__(self)

    def clear(self):
        BlockChildrenStash.clear(self)

    def unpack(self) -> dict[str, Any]:
        return dict(**BlockChildrenStash.unpack(self),
                    block_id=self.target_id)

    @drop_empty_request
    @retry_request
    def execute(self) -> dict:
        res = self.notion.blocks.children.append(**self.unpack())
        stopwatch(' '.join(['append', page_id_to_url(self.target_id)]))
        self.clear()
        return res


class UpdateBlock(Gateway):
    def __init__(self, editor: Editor):
        Gateway.__init__(self, editor)
        self._contents_value = None

    def __bool__(self):
        return self._contents_value is not None

    def clear(self):
        self._contents_value = None

    def apply_contents(self, carrier: ContentsEncoder):
        self._contents_value = carrier
        return carrier

    def unpack(self):
        return dict(**self._contents_value.unpack(),
                    block_id=self.target_id)

    @drop_empty_request
    @retry_request
    def execute(self) -> dict:
        if self._contents_value is None:
            return {}
        res = self.notion.blocks.update(**self.unpack())
        stopwatch(' '.join(['update', page_id_to_url(self.target_id)]))
        self.clear()
        return res

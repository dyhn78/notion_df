from typing import Any, Optional

from notion_py.interface.editor.common.struct import PointEditor
from notion_py.interface.encoder import ContentsEncoder
from .stash import BlockChildrenStash, PagePropertyStash
from ..struct import PointRequestor, print_response_error, drop_empty_request
from ...utility import stopwatch, page_id_to_url


class CreatePage(PointRequestor, PagePropertyStash, BlockChildrenStash):
    def __init__(self, editor: PointEditor, under_database: bool):
        PointRequestor.__init__(self, editor)
        PagePropertyStash.__init__(self)
        BlockChildrenStash.__init__(self)
        self.parent_type = 'database_id' if under_database else 'page_id'

    @property
    def target_id(self):
        return self.editor.parent_id

    @property
    def target_name(self):
        return self.editor.parent.master_name

    def __bool__(self):
        return any([PagePropertyStash.__bool__(self),
                    BlockChildrenStash.__bool__(self)])

    def clear(self):
        PagePropertyStash.clear(self)
        BlockChildrenStash.clear(self)

    def encode(self):
        res = dict(**PagePropertyStash.encode(self),
                   **BlockChildrenStash.encode(self),
                   parent={self.parent_type: self.target_id})
        return res

    @drop_empty_request
    @print_response_error
    def execute(self) -> dict:
        res = self.notion.pages.create(**self.encode())
        self.print_comments(res)
        return res

    def print_comments(self, res):
        target_url = page_id_to_url(res['id'])
        if self.target_name:
            form = ['create_page', f"< {self.target_name} >",
                    '\n\t', target_url]
        else:
            form = ['create_page', target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class UpdatePage(PointRequestor, PagePropertyStash):
    def __init__(self, editor: PointEditor):
        PointRequestor.__init__(self, editor)
        PagePropertyStash.__init__(self)
        self._archive_value = None

    def __bool__(self):
        return any([PagePropertyStash.__bool__(self),
                    self._archive_value is not None])

    def clear(self):
        PagePropertyStash.clear(self)
        self._archive_value = None

    def archive(self):
        self._archive_value = True

    def un_archive(self):
        self._archive_value = False

    def encode(self):
        res = dict(page_id=self.target_id,
                   **PagePropertyStash.encode(self))
        if self._archive_value is not None:
            res.update(archived=self._archive_value)
        return res

    @drop_empty_request
    @print_response_error
    def execute(self) -> dict:
        res = self.notion.pages.update(**self.encode())
        self.print_comments()
        return res

    def print_comments(self):
        target_url = page_id_to_url(self.target_id)
        if self.target_name:
            form = ['update_page', f"< {self.target_name} >",
                    '\n\t', target_url]
        else:
            form = ['update_page', target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class UpdateBlock(PointRequestor):
    def __init__(self, editor: PointEditor):
        PointRequestor.__init__(self, editor)
        self._contents_value: Optional[ContentsEncoder] = None
        self._archive_value = None

    def __bool__(self):
        return any([self._contents_value is not None,
                    self._archive_value is not None])

    def clear(self):
        self._contents_value = None
        self._archive_value = None

    def archive(self):
        self._archive_value = True

    def un_archive(self):
        self._archive_value = False

    def apply_contents(self, carrier: ContentsEncoder):
        self._contents_value = carrier
        return carrier

    def encode(self):
        res = dict(block_id=self.target_id)
        if self._contents_value is not None:
            res.update(**self._contents_value.encode())
        if self._archive_value is not None:
            res.update(archived=self._archive_value)
        return res

    @drop_empty_request
    @print_response_error
    def execute(self) -> dict:
        res = self.notion.blocks.update(**self.encode())
        self.print_comments()
        return res

    def print_comments(self):
        target_url = page_id_to_url(self.target_id)
        if self.target_name:
            form = ['update_block', f"< {self.target_name} >",
                    '\n\t', target_url]
        else:
            form = ['update_block', target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class AppendBlockChildren(PointRequestor, BlockChildrenStash):
    def __init__(self, editor: PointEditor):
        PointRequestor.__init__(self, editor)
        BlockChildrenStash.__init__(self)

    def __bool__(self):
        return BlockChildrenStash.__bool__(self)

    def encode(self) -> dict[str, Any]:
        return dict(**BlockChildrenStash.encode(self),
                    block_id=self.target_id)

    @drop_empty_request
    @print_response_error
    def execute(self) -> dict:
        res = self.notion.blocks.children.append(**self.encode())
        self.print_comments()
        return res

    def clear(self):
        BlockChildrenStash.clear(self)

    def print_comments(self):
        target_url = page_id_to_url(self.target_id)
        if self.target_name:
            form = ['append_block', f"< {self.target_name} >",
                    '\n\t', target_url]
        else:
            form = ['append_block', target_url]
        comments = ' '.join(form)
        stopwatch(comments)

from typing import Any, Optional

from notion_zap.cli.core.base import Component
from notion_zap.cli.utility import stopwatch, id_to_url
from .stash import BlockChildrenStash, PagePropertyStash
from ..structs import Requestor, print_response_error, drop_empty_request
from ...encoders import ContentsEncoder


class CreatePage(Requestor, PagePropertyStash, BlockChildrenStash):
    def __init__(self, editor: Component, under_database: bool):
        Requestor.__init__(self, editor)
        PagePropertyStash.__init__(self)
        BlockChildrenStash.__init__(self)
        self.parent_type = 'database_id' if under_database else 'page_id'
        self._res = None

    @property
    def parent_id(self):
        return self.editor.parent_id

    @property
    def parent_name(self):
        return self.editor.parent.block_name

    def __bool__(self):
        return any([PagePropertyStash.__bool__(self),
                    BlockChildrenStash.__bool__(self)])

    def clear(self):
        PagePropertyStash.clear(self)
        BlockChildrenStash.clear(self)

    def encode(self):
        res = dict(**PagePropertyStash.encode(self),
                   **BlockChildrenStash.encode(self),
                   parent={self.parent_type: self.parent_id})
        return res

    @drop_empty_request
    @print_response_error
    def execute(self) -> dict:
        res = self.client.pages.create(**self.encode())
        self._res = res
        self.print_comments()
        return res

    def print_comments(self):
        super().print_comments()
        target_url = id_to_url(self._res['id'])
        if self.target_name:
            form = ['create_page', f"< {self.target_name} >",
                    '\n\t', target_url]
        else:
            form = ['create_page_at', f"< {self.parent_name} >",
                    '\n\t', target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class UpdatePage(Requestor, PagePropertyStash):
    def __init__(self, editor: Component):
        Requestor.__init__(self, editor)
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
        res = self.client.pages.update(**self.encode())
        self.print_comments()
        return res

    def print_comments(self):
        super().print_comments()
        if self.target_name:
            form = ['update_page', f"< {self.target_name} >",
                    '\n\t', self.target_url]
        else:
            form = ['update_page', self.target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class UpdateBlock(Requestor):
    def __init__(self, editor: Component):
        Requestor.__init__(self, editor)
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
        res = self.client.blocks.update(**self.encode())
        self.print_comments()
        return res

    def print_comments(self):
        super().print_comments()
        if self.target_name:
            form = ['update_block', f"< {self.target_name} >",
                    '\n\t', self.target_url]
        else:
            form = ['update_block', self.target_url]
        comments = ' '.join(form)
        stopwatch(comments)

    @print_response_error
    def delete(self):
        res = self.client.blocks.delete(self.target_id)
        self.print_comments()
        return res


class AppendBlockChildren(Requestor, BlockChildrenStash):
    def __init__(self, editor: Component):
        Requestor.__init__(self, editor)
        BlockChildrenStash.__init__(self)

    def __bool__(self):
        return BlockChildrenStash.__bool__(self)

    def encode(self) -> dict[str, Any]:
        return dict(**BlockChildrenStash.encode(self),
                    block_id=self.target_id)

    @drop_empty_request
    @print_response_error
    def execute(self) -> dict:
        res = self.client.blocks.children.append(**self.encode())
        self.print_comments()
        return res

    def clear(self):
        BlockChildrenStash.clear(self)

    def print_comments(self):
        super().print_comments()
        if self.target_name:
            form = ['append_block', f"< {self.target_name} >",
                    '\n\t', self.target_url]
        else:
            form = ['append_block', self.target_url]
        comments = ' '.join(form)
        stopwatch(comments)

from __future__ import annotations

from typing import Union

from notion_py.interface.api_encode import RichTextContentsEncoder
from notion_py.interface.api_parse import BlockChildrenParser
from notion_py.interface.gateway import AppendBlockChildren
from notion_py.interface.struct import PointEditor, GroundEditor


class BlockSphereCreator(GroundEditor):
    def __init__(self, caller: PointEditor):
        from ...inline.page import InlinePageBlock
        from .abs_contents_bearing.master import ContentsBearingBlock
        super().__init__(caller)
        self._chunks: list[list[ContentsBearingBlock]] = []
        self._requests: list[Union[AppendBlockChildren, InlinePageBlock]] = []
        self.gateway = AppendBlockChildren(self)
        self._chunk_interrupted = True

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any(child for child in self)

    @property
    def values(self):
        res = []
        for chunk in self._chunks:
            res.extend(chunk)
        return res

    def make_preview(self):
        from ...inline.page import InlinePageBlock
        res = []
        for request in self._requests:
            if isinstance(request, AppendBlockChildren):
                res.append(request.unpack())
            elif isinstance(request, InlinePageBlock):
                res.append(request.make_preview())
        return res

    def execute(self):
        from ...inline.page import InlinePageBlock
        for request, chunk in zip(self._requests, self._chunks):
            if isinstance(request, AppendBlockChildren):
                response = request.execute()
                if not response:
                    continue
                parsers = BlockChildrenParser(response)
                for parser, new_child in zip(parsers, chunk):
                    new_child.contents.apply_block_parser(parser)
            elif isinstance(request, InlinePageBlock):
                request.execute()
            else:
                raise ValueError(request)
        for child in self.values:
            child.execute()
        res = self.values.copy()
        self.values.clear()
        self._requests.clear()
        return res

    def create_text_block(self):
        from ...inline.text_block import TextBlock
        if self._chunk_interrupted:
            self.gateway = AppendBlockChildren(self)
            self._requests.append(self.gateway)
            self._chunks.append([])
            self._chunk_interrupted = False
        child = TextBlock.create_new(self)
        self._chunks[-1].append(child)
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child

    def create_page_block(self):
        from ...inline.page import InlinePageBlock
        child = InlinePageBlock.create_new(self)
        self._requests.append(child)
        self._chunks.append([child])
        self._chunk_interrupted = True
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child

    def push_carrier(self, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)

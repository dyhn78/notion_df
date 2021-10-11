from __future__ import annotations

from typing import Union

from .sphere import BlockSphere
from ...struct import GroundEditor
from notion_py.interface.encoder import RichTextContentsEncoder
from notion_py.interface.parser import BlockChildrenParser
from notion_py.interface.requestor import AppendBlockChildren


class BlockSphereCreator(GroundEditor):
    def __init__(self, caller: BlockSphere):
        from ...inline.page_block import InlinePageBlock
        from .abs_contents_bearing.master import ContentsBearingBlock
        super().__init__(caller)
        self.caller = caller
        self.gateway = AppendBlockChildren(self)
        self._chunks: list[list[ContentsBearingBlock]] = []
        self._requests: list[Union[AppendBlockChildren, InlinePageBlock]] \
            = [self.gateway]
        self._chunk_interrupted = True
        self._execute_in_process = False

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

    def preview(self):
        from ...inline.page_block import InlinePageBlock
        res = []
        for request in self._requests:
            if isinstance(request, AppendBlockChildren):
                res.append(request.unpack())
            elif isinstance(request, InlinePageBlock):
                res.append(request.preview())
        return res

    def execute(self):
        if self._execute_in_process:
            return
            # message = ("child block yet not created ::\n"
            #            f"{[value.fully_read() for value in self.values]}")
            # raise RecursionError(message)
        self._execute_in_process = True
        from ...inline.page_block import InlinePageBlock
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
        self._execute_in_process = False
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
        from ...inline.page_block import InlinePageBlock
        child = InlinePageBlock.create_new(self)
        self._requests.append(child)
        self._chunks.append([child])
        self._chunk_interrupted = True
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child

    def push_carrier(self, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)

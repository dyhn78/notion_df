from __future__ import annotations

from typing import Union

from notion_py.interface.editor.common.struct import (
    PointEditor)
from notion_py.interface.encoder import RichTextContentsEncoder
from notion_py.interface.parser import BlockChildrenParser
from notion_py.interface.requestor import AppendBlockChildren
from .bearer import ItemAttachments
from ..struct.agents import GroundEditor, AdaptiveEditor


class ItemsCreator(PointEditor):
    def __init__(self, caller: ItemAttachments):
        super().__init__(caller)
        self.caller = caller
        self.agents: list[Union[TextItemsCreateAgent,
                                PageItemCreateAgent]] = []
        self._execute_in_process = False
        self.enable_overwrite = True

    def create_text_item(self):
        if (self.agents and
                isinstance(self.agents[-1], TextItemsCreateAgent)):
            agent = self.agents[-1]
        else:
            agent = TextItemsCreateAgent(self)
            self.agents.append(agent)
        return agent.add()

    def create_page_item(self):
        agent = PageItemCreateAgent(self)
        self.agents.append(agent)
        return agent.block

    def clear(self):
        self.agents = []

    def save_required(self):
        return bool(self.agents)

    def save_info(self):
        res = []
        for unit in self.agents:
            res.append(unit.save_info())
        return res

    def save(self):
        if self._execute_in_process:
            # message = ("child block yet not created ::\n"
            #            f"{[value.fully_read() for value in self.blocks]}")
            # raise RecursionError(message)
            return []
        self._execute_in_process = True
        for agent in self.agents:
            agent.save()
        self._execute_in_process = False
        return self.blocks

    @property
    def blocks(self):
        res = []
        for agent in self.agents:
            res.extend(agent.blocks)
        return res

    def __iter__(self):
        return iter(self.blocks)

    def __len__(self):
        return len(self.blocks)


class TextItemsCreateAgent(GroundEditor):
    def __init__(self, caller: ItemsCreator):
        super().__init__(caller)
        self._requestor = AppendBlockChildren(self)

        from ...inline.text_item import TextItem
        self.blocks: list[TextItem] = []

    @property
    def requestor(self) -> AppendBlockChildren:
        return self._requestor

    def add(self):
        from ...inline.text_item import TextItem
        child = TextItem(self, '')
        self.blocks.append(child)
        self.requestor.append_space()
        return child

    def push_carrier(self, child, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        i = self.blocks.index(child)
        return self.requestor.apply_contents(i, carrier)

    def save(self):
        response = self.requestor.execute()
        parsers = BlockChildrenParser(response)
        for child, parser in zip(self.blocks, parsers):
            child.contents.apply_block_parser(parser)
            child.save_this()


class PageItemCreateAgent(AdaptiveEditor):
    def __init__(self, caller: ItemsCreator):
        super().__init__(caller)
        self.caller = caller

        from ...inline.page_item import PageItem
        self.block = PageItem(self, '')

    @property
    def value(self):
        return self.block

    @property
    def blocks(self):
        return [self.block]

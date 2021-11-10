from __future__ import annotations

from typing import Union

from notion_py.interface.gateway.encoders import ContentsEncoder
from notion_py.interface.gateway.parsers import BlockChildrenParser
from notion_py.interface.gateway.requestors import AppendBlockChildren
from .bearer import ItemAttachments
from notion_py.interface.editor.struct import (
    BlockEditor, GroundEditor, AdaptiveEditor)


class ItemsCreator(BlockEditor):
    def __init__(self, caller: ItemAttachments):
        super().__init__(caller)
        self.caller = caller
        self.agents: list[Union[TextItemsCreateAgent,
                                PageItemCreateAgent]] = []
        self._execute_in_process = False

    def attach_page_item(self, child):
        from ...inline.page_item import PageItem
        assert isinstance(child, PageItem)
        agent = PageItemCreateAgent(self, child)
        self.agents.append(agent)

    def attach_text_item(self, child):
        from ...inline.text_item import TextItem
        assert isinstance(child, TextItem)
        agent = self._get_text_agent()
        agent.attach(child)

    def _get_text_agent(self):
        if (self.agents and
                isinstance(self.agents[-1], TextItemsCreateAgent)):
            agent = self.agents[-1]
        else:
            agent = TextItemsCreateAgent(self)
            self.agents.append(agent)
        return agent

    def clear(self):
        self.agents = []

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

    def save_info(self):
        res = []
        for unit in self.agents:
            res.append(unit.save_info())
        return res

    def save_required(self):
        return bool(self.agents)

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
    def requestor(self):
        return self._requestor

    def attach(self, child):
        from ...inline.text_item import TextItem
        assert isinstance(child, TextItem)

        self.blocks.append(child)
        child.contents.set_callback(self.get_callback_func(child))
        child.contents.set_placeholder()

    def get_callback_func(self, child):
        idx = self.blocks.index(child)

        def callback(carrier: ContentsEncoder):
            return self.requestor.apply_contents(idx, carrier)
        return callback

    def save(self):
        response = self.requestor.execute()
        parsers = BlockChildrenParser(response)
        for child, parser in zip(self.blocks, parsers):
            child.contents.apply_block_parser(parser)
            child.save_this()


class PageItemCreateAgent(AdaptiveEditor):
    def __init__(self, caller: ItemsCreator, child):
        super().__init__(caller)
        self.caller = caller
        self._value = child

    @property
    def value(self):
        return self._value

    @property
    def blocks(self):
        return [self._value]

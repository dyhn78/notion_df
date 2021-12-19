from __future__ import annotations

from typing import Union

from .main import ItemChildren
from ...structs.save_agents import SingularEditor, RequestEditor
from ...structs.base_logic import Saveable
from ...structs.block_main import Follower
from notion_zap.cli.gateway.encoders import ContentsEncoder
from notion_zap.cli.gateway.parsers import BlockChildrenParser
from notion_zap.cli.gateway.requestors import AppendBlockChildren


class ItemsCreator(Follower, Saveable):
    def __init__(self, caller: ItemChildren):
        super().__init__(caller)
        self.agents: list[Union[TextItemsCreateAgent,
                                PageItemCreateAgent]] = []

    @property
    def values(self):
        res = []
        for agent in self.agents:
            res.extend(agent.values)
        return res

    def attach_page_item(self, child):
        from ...items.page_item import PageItem
        assert isinstance(child, PageItem)
        agent = PageItemCreateAgent(self.block, child)
        self.agents.append(agent)

    def attach_text_item(self, child):
        from ...items.text_item import TextItem
        assert isinstance(child, TextItem)
        agent = self._get_text_agent()
        agent.attach(child)

    def _get_text_agent(self):
        if (self.agents and
                isinstance(self.agents[-1], TextItemsCreateAgent)):
            agent = self.agents[-1]
        else:
            agent = TextItemsCreateAgent(self.block)
            self.agents.append(agent)
        return agent

    def clear(self):
        self.agents = []

    def save(self):
        for agent in self.agents:
            agent.save()
        return self.values

    def save_info(self):
        res = []
        for unit in self.agents:
            res.append(unit.save_info())
        return res

    def save_required(self):
        return bool(self.agents)


class TextItemsCreateAgent(Follower, RequestEditor):
    def __init__(self, caller):
        super().__init__(caller)
        self._requestor = AppendBlockChildren(self)

        from ...items.text_item import TextItem
        self.values: list[TextItem] = []

    @property
    def requestor(self) -> AppendBlockChildren:
        return self._requestor

    def attach(self, child):
        from ...items.text_item import TextItem
        assert isinstance(child, TextItem)

        self.values.append(child)
        child.set_callback(self.get_callback_func(child))
        child.set_placeholder()

    def get_callback_func(self, child):
        idx = self.values.index(child)

        def callback(carrier: ContentsEncoder):
            return self.requestor.apply_contents(idx, carrier)

        return callback

    def save(self):
        response = self.requestor.execute()
        parsers = BlockChildrenParser(response)
        for child, parser in zip(self.values, parsers):
            child.apply_block_parser(parser)
            child.save()


class PageItemCreateAgent(SingularEditor):
    def __init__(self, block, child):
        super().__init__(block)
        self._value = child

    @property
    def value(self):
        return self._value

    @property
    def values(self):
        return [self._value]

from __future__ import annotations

from typing import Union, Any

from .leaders import ItemChildren
from ...structs.followers import RequestEditor, SingularEditor
from ...structs.leaders import Follower
from notion_zap.cli.gateway.encoders import ContentsEncoder
from notion_zap.cli.gateway.parsers import BlockChildrenParser
from notion_zap.cli.gateway.requestors import AppendBlockChildren


class ItemsCreator(Follower):
    def __init__(self, caller: ItemChildren):
        super().__init__(caller)
        self.caller = caller
        self.agents: list[Union[TextItemsCreateAgent,
                                PageItemCreateAgent]] = []
        self._execute_in_process = False

    @property
    def values(self):
        res = []
        for agent in self.agents:
            res.extend(agent.values)
        return res

    def attach_page_item(self, child):
        from ...items.page_item import PageItem
        assert isinstance(child, PageItem)
        agent = PageItemCreateAgent(self, child)
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
            agent = TextItemsCreateAgent(self)
            self.agents.append(agent)
        return agent

    def clear(self):
        self.agents = []

    def save(self):
        if self._execute_in_process:
            return []
        self._execute_in_process = True
        for agent in self.agents:
            agent.save()
        self._execute_in_process = False
        return self.values

    def save_info(self):
        res = []
        for unit in self.agents:
            res.append(unit.save_info())
        return res

    def save_required(self):
        return bool(self.agents)


class TextItemsCreateAgent(RequestEditor):
    def __init__(self, caller: ItemsCreator):
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
        child.contents.set_callback(self.get_callback_func(child))
        child.contents.set_placeholder()

    def get_callback_func(self, child):
        idx = self.values.index(child)

        def callback(carrier: ContentsEncoder):
            return self.requestor.apply_contents(idx, carrier)

        return callback

    def save(self):
        response = self.requestor.execute()
        parsers = BlockChildrenParser(response)
        for child, parser in zip(self.values, parsers):
            child.contents.apply_block_parser(parser)
            child.save_this()


class PageItemCreateAgent(SingularEditor):
    def __init__(self, caller: ItemsCreator, child):
        super().__init__(caller)
        self.caller = caller
        self._value = child

    @property
    def value(self):
        return self._value

    @property
    def values(self):
        return [self._value]

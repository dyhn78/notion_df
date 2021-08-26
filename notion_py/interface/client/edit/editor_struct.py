from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Optional

from notion_py.interface.struct import Requestor


class Editor(Requestor, metaclass=ABCMeta):
    @abstractmethod
    def set_overwrite_option(self, option: bool):
        pass


class MasterEditor(Editor, metaclass=ABCMeta):
    def __init__(self, master_id: str, caller: Optional[BridgeEditor] = None):
        self.caller = caller
        self.master_id = master_id
        self.set_overwrite_option(True)
        self.agents: dict[str, Editor] = {}

    def __iter__(self):
        return self.agents.values()

    def __len__(self):
        return len(self.agents)

    def __bool__(self):
        return any(agent for agent in self)

    def set_overwrite_option(self, option: bool):
        for requestor in self.agents.values():
            requestor.set_overwrite_option(option)

    def unpack(self):
        return {key: value.unpack() for key, value in self.agents}

    def execute(self):
        return {key: value.execute() for key, value in self.agents}


class BridgeEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: MasterEditor):
        self.caller = caller
        self.values: list[MasterEditor] = []

    def __iter__(self):
        return self.values

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any(child for child in self)

    def set_overwrite_option(self, option: bool):
        for child in self:
            child.set_overwrite_option(option)

    def unpack(self):
        return [child.unpack() for child in self]

    def execute(self):
        return [child.execute() for child in self]


class GatewayEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: MasterEditor):
        self.caller = caller
        self.gateway: Optional[Requestor] = None
        self.enable_overwrite = True

    def __bool__(self):
        return bool(self.gateway)

    def set_overwrite_option(self, option: bool):
        self.enable_overwrite = option

    def unpack(self):
        return self.gateway.unpack()

    def execute(self):
        return self.gateway.execute()


"""
from itertools import chain
from typing import ValuesView, Mapping

class AbstractMasterEditor(Requestor):
    def __init__(self, master_id: str):
        self.master_id = master_id
        self.set_overwrite_option(True)

    @abstractmethod
    def set_overwrite_option(self, option: bool):
        pass

class EditorComponentStash(dict):
    def __init__(self, caller: EditorControl):
        super().__init__()
        self.caller = caller

    def values(self) -> ValuesView[EditorComponent]:
        return super().values()

    def update(self, __m: Mapping[str, EditorComponent],
               **kwargs: dict[str, EditorComponent]):
        super().update(__m, **kwargs)
        for key, value in chain(__m, kwargs):
            setattr(self.caller, key, value)


class StackEditor(AbstractMainEditor):
    def __init__(self, master_id: str):
        super().__init__(master_id)
        self.elements: list[MainEditor] = []

    def __iter__(self) -> list[MainEditor]:
        return self.elements

    def set_overwrite_option(self, option: bool):
        for child in self:
            child.set_overwrite_option(option)

    def unpack(self):
        return [child.unpack() for child in self]

    def execute(self):
        return [child.execute() for child in self]
"""

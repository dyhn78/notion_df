from __future__ import annotations
from abc import ABCMeta, abstractmethod
from pprint import pprint
from typing import Union
from notion_client import Client, AsyncClient

from .carrier import Requestor
from ..utility import page_id_to_url


class Editor(Requestor, metaclass=ABCMeta):
    def __init__(self, root_editor: AbstractRootEditor):
        self.root_editor = root_editor

    @abstractmethod
    def preview(self):
        pass

    def pprint(self, **kwargs):
        pprint(self.preview(), **kwargs)


class AbstractRootEditor(Editor):
    @abstractmethod
    def __init__(self):
        super().__init__(self)
        self.notion: Union[Client, AsyncClient, None] = None


class PointEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: Union[PointEditor, Editor]):
        self.caller = caller
        super().__init__(caller.root_editor)

    @property
    def master(self) -> MasterEditor:
        return self.caller.master

    @property
    def parent(self) -> MasterEditor:
        return self.master.caller.master

    @property
    def master_id(self) -> str:
        return self.master.master_id

    @master_id.setter
    def master_id(self, value: str):
        self.master.master_id = value

    @property
    def parent_id(self) -> str:
        return self.parent.master_id

    @parent_id.setter
    def parent_id(self, value: str):
        self.parent.master_id = value

    @property
    def master_url(self):
        return page_id_to_url(self.master_id)

    @property
    def yet_not_created(self):
        if self.master_id:
            return False
        else:
            assert self.parent_id
            return True


class MasterEditor(PointEditor):
    def __init__(self, caller: Union[PointEditor, Editor], master_id: str):
        super().__init__(caller)
        self.agents: dict[str, Union[PointEditor]] = {}
        self.master_id = master_id
        self.set_overwrite_option(True)
        self.is_supported_type = False
        self.can_have_children = False
        self.has_children = False

    def __bool__(self):
        return any(agent for agent in self.agents.values())

    @property
    def master(self):
        return self

    @property
    @abstractmethod
    def master_name(self):
        pass

    @property
    def master_id(self):
        return self._master_id

    @master_id.setter
    def master_id(self, value):
        self._master_id = value

    @property
    def parent_id(self):
        try:
            return self.parent.master_id
        except AttributeError:
            if self.master_url:
                message = f'cannot find parent_id at: {self.master_url}'
            else:
                message = (f"ERROR: provide master_id or parent_id for this block;\n"
                           f"editor info:\n"
                           f"{self.preview()}")
            raise AttributeError(message)

    def set_overwrite_option(self, option: bool):
        for requestor in self.agents.values():
            if hasattr(requestor, 'set_overwrite_option'):
                requestor.set_overwrite_option(option)

    @abstractmethod
    def preview(self):
        return {key: value.preview() for key, value in self.agents.items()}

    @abstractmethod
    def execute(self):
        return {key: value.execute() for key, value in self.agents.items()}

    @abstractmethod
    def fully_read(self):
        pass

    @abstractmethod
    def fully_read_rich(self):
        pass


class BridgeEditor(PointEditor, metaclass=ABCMeta):
    def __init__(self, caller: PointEditor):
        super().__init__(caller)
        self.values: list[MasterEditor] = []

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any([child for child in self.values])

    def set_overwrite_option(self, option: bool):
        for child in self:
            child.set_overwrite_option(option)

    def preview(self):
        return [child.preview() for child in self.values]

    def execute(self):
        return [child.execute() for child in self.values]


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

from abc import ABCMeta, abstractmethod

from .leaders import Component, Block
from notion_zap.cli.gateway.requestors.structs import Requestor


class Follower(Component, metaclass=ABCMeta):
    def __init__(self, caller: Component):
        self.caller = caller

    @property
    def block(self) -> Block:
        return self.caller.block

    @property
    def block_id(self) -> str:
        return self.block.block_id

    @property
    def block_name(self) -> str:
        return self.block.block_name

    @property
    def archived(self):
        return self.block.archived


class ListEditor(Follower, metaclass=ABCMeta):
    @property
    @abstractmethod
    def values(self) -> list[Block]:
        pass

    def save(self):
        return [child.save() for child in self.values]

    def save_info(self):
        return [child.save_info() for child in self.values]

    def save_required(self):
        return any([child for child in self.values])

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __getitem__(self, index: int):
        return self.values[index]


class RequestEditor(Follower, metaclass=ABCMeta):
    @property
    @abstractmethod
    def requestor(self) -> Requestor:
        pass

    def save(self):
        return self.requestor.execute()

    def save_info(self):
        return self.requestor.encode()

    def save_required(self):
        return self.requestor.__bool__()


class SingularEditor(Follower, metaclass=ABCMeta):
    @property
    @abstractmethod
    def value(self) -> Component:
        pass

    def save(self):
        return self.value.save()

    def save_info(self):
        return self.value.save_info()

    def save_required(self):
        return self.value.save_required()


"""
from itertools import chain
from typing import ValuesView, Mapping

class AbstractMasterEditor(Executable):
    def __init__(self, block_id: str):
        self.block_id = block_id
        self.set_overwrite_option(True)

    @abstractmethod
    def set_overwrite_option(self, option: bool):
        pass

class EditorComponentStash(dict):
    def __init__(self, caller: EditorControl):
        super().__init__()
        self.caller = caller

    def blocks(self) -> ValuesView[EditorComponent]:
        return super().blocks()

    def update(self, __m: Mapping[str, EditorComponent],
               **kwargs: dict[str, EditorComponent]):
        super().update(__m, **kwargs)
        for key, value in chain(__m, kwargs):
            setattr(self.caller, key, value)


class StackEditor(AbstractMainEditor):
    def __init__(self, block_id: str):
        super().__init__(block_id)
        self.row: list[MainEditor] = []

    def __iter__(self) -> list[MainEditor]:
        return self.row

    def set_overwrite_option(self, option: bool):
        for child in self:
            child.set_overwrite_option(option)

    def unpack(self):
        return [child.unpack() for child in self]

    def execute(self):
        return [child.execute() for child in self]
"""

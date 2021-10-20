from __future__ import annotations

from abc import ABC, abstractmethod, ABCMeta
from pprint import pprint


class Printable(ABC):
    @abstractmethod
    def pprint(self, **kwargs):
        pass


class Executable(Printable, metaclass=ABCMeta):
    @abstractmethod
    def execute(self):
        pass


class Editor(Executable, metaclass=ABCMeta):
    def __init__(self, root_editor):
        from notion_py.interface import RootEditor
        self.root: RootEditor = root_editor

    @abstractmethod
    def has_updates(self):
        pass

    @abstractmethod
    def preview(self):
        pass

    def pprint(self, **kwargs):
        pprint(self.preview(), **kwargs)


class ValueCarrier(Printable, metaclass=ABCMeta):
    @abstractmethod
    def __bool__(self):
        pass

    @abstractmethod
    def unpack(self):
        pass

    def pprint(self, **kwargs):
        pprint(self.unpack(), **kwargs)


class Requestor(Executable, ValueCarrier, metaclass=ABCMeta):
    pass

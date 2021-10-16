from __future__ import annotations

from abc import ABC, abstractmethod, ABCMeta
from pprint import pprint
from typing import Union, Callable

from notion_client import Client, AsyncClient


class Printable(ABC):
    @abstractmethod
    def pprint(self, **kwargs):
        pass


class Executable(Printable, metaclass=ABCMeta):
    @abstractmethod
    def __bool__(self):
        pass

    @abstractmethod
    def execute(self):
        pass


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
    def pprint(self, **kwargs):
        return ValueCarrier.pprint(self, **kwargs)


class Editor(Executable, metaclass=ABCMeta):
    def __init__(self, root_editor):
        from notion_py.interface import RootEditor
        self.root_editor: RootEditor = root_editor

    @abstractmethod
    def preview(self):
        pass

    def pprint(self, **kwargs):
        pprint(self.preview(), **kwargs)


def drop_empty_request(method: Callable):
    def wrapper(self, **kwargs):
        if not bool(self):
            return {}
        return method(self, **kwargs)

    return wrapper

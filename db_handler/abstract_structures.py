from __future__ import annotations
from abc import abstractmethod, ABC, ABCMeta
from typing import Union, Type

from notion_client import Client, AsyncClient


class AbstractInterface(ABC):
    @property
    @abstractmethod
    def apply(self) -> dict:
        pass

    def __bool__(self):
        return bool(self.apply)


class Requestor(AbstractInterface):
    def __init__(self, notion: Union[Client, AsyncClient]):
        self.notion = notion

    @abstractmethod
    def execute(self):
        pass


class ValueReceiver(AbstractInterface):
    def __init__(self):
        self.storage = None

    @property
    def apply(self):
        return self.storage.apply

    def clear(self):
        self.storage = None

    def save(self, handler):
        self.storage = handler


class ValueStack(AbstractInterface, metaclass=ABCMeta):
    def __init__(self, sender_class: Type[ValueStack]):
        self.storage = []
        self.sender_class = sender_class

    def clear(self):
        self.storage = []


class ListtypeStack(ValueStack):
    @property
    def apply(self):
        return [handler.apply for handler in self.storage]

    def append(self, handler):
        self.storage.append(handler)

    def appendleft(self, handler):
        self.storage.insert(0, handler)

    def create(self):
        handler = self.sender_class.__init__(self)
        self.append(handler)

    def createleft(self):
        handler = self.sender_class.__init__(self)
        self.appendleft(handler)


class DicttypeStack(ValueStack):
    @property
    def apply(self):
        res = {}
        for handler in self.storage:
            for key, value in handler.apply:
                res[key] = value
        return res

    def add(self, handler):
        self.storage.append(handler)

    def create(self):
        handler = self.sender_class.__init__(self)
        self.add(handler)

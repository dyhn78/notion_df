from __future__ import annotations

from abc import ABC, abstractmethod, ABCMeta
from pprint import pprint


class Printable(ABC):
    @abstractmethod
    def preview(self, **kwargs):
        pass


class Executable(Printable, metaclass=ABCMeta):
    @abstractmethod
    def execute(self):
        pass


class ValueCarrier(Printable, metaclass=ABCMeta):
    @abstractmethod
    def __bool__(self):
        pass

    @abstractmethod
    def encode(self):
        pass

    def preview(self, **kwargs):
        pprint(self.encode(), **kwargs)


class Requestor(Executable, ValueCarrier, metaclass=ABCMeta):
    pass

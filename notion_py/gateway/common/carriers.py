from __future__ import annotations
from abc import abstractmethod, ABC, ABCMeta


class Structure(ABC):
    @abstractmethod
    def apply(self) -> dict:
        pass

    def __bool__(self):
        return bool(self.apply())


class ValueReceiver(Structure):
    def __init__(self):
        self.__value = None

    def apply(self):
        return self.__value.apply()

    def clear(self):
        self.__value = None

    def save(self, handler):
        self.__value = handler


class ValueCarrier(Structure, metaclass=ABCMeta):
    pass


class Stash(ValueCarrier, metaclass=ABCMeta):
    def __init__(self):
        self._subdicts = []

    def __bool__(self):
        return bool(self._subdicts)

    def clear(self):
        self._subdicts = []


class ListStash(Stash, metaclass=ABCMeta):
    def _unpack(self):
        return self._subdicts


class DictStash(Stash, metaclass=ABCMeta):
    def _unpack(self):
        res = {}
        for subdict in self._subdicts:
            for key, value in subdict.items():
                res[key] = value
        return res



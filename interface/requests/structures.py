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

    def stash(self, plaindict: dict):
        self._subdicts.append(plaindict)
        return plaindict

    def stashleft(self, carrier: dict):
        self._subdicts.insert(0, carrier)
        return carrier


class DictStash(Stash, metaclass=ABCMeta):
    def _unpack(self):
        res = {}
        for subdict in self._subdicts:
            for key, value in subdict.items():
                res[key] = value
        return res

    def stash(self, subdict: dict):
        self._subdicts.append(subdict)
        return subdict


class TwofoldStash(ValueCarrier, metaclass=ABCMeta):
    def __init__(self):
        self.subcarriers = []

    def __bool__(self):
        return bool(self.subcarriers)

    def clear(self):
        self.subcarriers = []


class TwofoldListStash(TwofoldStash, metaclass=ABCMeta):
    def _unpack(self):
        return [carrier.apply() for carrier in self.subcarriers]

    def stash(self, carrier: ValueCarrier):
        self.subcarriers.append(carrier)
        return carrier

    def stashleft(self, carrier: ValueCarrier):
        self.subcarriers.insert(0, carrier)
        return carrier


class TwofoldDictStash(TwofoldStash, metaclass=ABCMeta):
    def _unpack(self):
        res = {}
        for carrier in self.subcarriers:
            for key, value in carrier.apply().items():
                res[key] = value
        return res

    def stash(self, carrier: ValueCarrier):
        self.subcarriers.append(carrier)
        return carrier

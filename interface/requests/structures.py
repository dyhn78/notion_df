from __future__ import annotations
from abc import abstractmethod, ABC, ABCMeta
from typing import Type


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
    def __init__(self):
        self.subcarriers = []

    def __bool__(self):
        return bool(self.subcarriers)

    def clear(self):
        self.subcarriers = []

    @abstractmethod
    def stash(self):
        pass


class ListStash(ValueCarrier, metaclass=ABCMeta):
    def stash(self):
        return [carrier.apply() for carrier in self.subcarriers]

    def append_to_liststash(self, carrier: ValueCarrier):
        self.subcarriers.append(carrier)
        return carrier

    def appendleft_to_liststash(self, carrier: ValueCarrier):
        self.subcarriers.insert(0, carrier)
        return carrier


class UniformListStash(ListStash, metaclass=ABCMeta):
    def __init__(self, frame_class: Type[ValueCarrier]):
        super().__init__()
        self.frame_class = frame_class

    def create_and_append_to_liststash(self):
        carrier = self.frame_class()
        self.append_to_liststash(carrier)
        return carrier

    def create_and_appendleft_to_liststash(self):
        carrier = self.frame_class()
        self.appendleft_to_liststash(carrier)
        return carrier


class DictStash(ValueCarrier, metaclass=ABCMeta):
    def stash(self):
        res = {}
        for carrier in self.subcarriers:
            for key, value in carrier.apply().items():
                res[key] = value
        return res

    def add_to_dictstash(self, carrier: ValueCarrier):
        self.subcarriers.append(carrier)
        return carrier


class UniformDictStash(DictStash, metaclass=ABCMeta):
    def __init__(self, frame_class: Type[ValueCarrier]):
        super().__init__()
        self.frame_class = frame_class

    def create_and_add_to_dictstash(self):
        carrier = self.frame_class()
        self.add_to_dictstash(carrier)
        return carrier


class PlainCarrier(ValueCarrier):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def stash(self):
        return self.value

    def apply(self):
        return self.value

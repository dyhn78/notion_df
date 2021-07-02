from __future__ import annotations
from abc import abstractmethod, ABC, ABCMeta
from typing import Union, Type

from notion_client import Client, AsyncClient


class Structure(ABC):
    @abstractmethod
    def apply(self) -> dict:
        pass

    def __bool__(self):
        return bool(self.apply())


class Requestor(Structure):
    def __init__(self, notion: Union[Client, AsyncClient]):
        self.notion = notion

    @abstractmethod
    def execute(self):
        pass


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
        return [handler.apply() for handler in self.subcarriers]

    def append(self, handler):
        self.subcarriers.append(handler)
        return handler

    def appendleft(self, handler):
        self.subcarriers.insert(0, handler)
        return handler


class DictStash(ValueCarrier, metaclass=ABCMeta):
    def stash(self):
        res = {}
        for handler in self.subcarriers:
            for hkey, hvalue in handler.apply():
                res[hkey] = hvalue
        return res

    def edit(self, handler):
        self.subcarriers.append(handler)
        return handler


class UniformListStash(ListStash, metaclass=ABCMeta):
    def __init__(self, frame_class: Type[Structure]):
        super().__init__()
        self.frame_class = frame_class

    def create(self):
        handler = self.frame_class()
        self.append(handler)
        return handler

    def createleft(self):
        handler = self.frame_class()
        self.appendleft(handler)
        return handler


class UniformDictStash(DictStash, metaclass=ABCMeta):
    def __init__(self, frame_class: Type[Structure]):
        super().__init__()
        self.frame_class = frame_class

    def add(self):
        handler = self.frame_class()
        self.edit(handler)
        return handler


class PlainCarrier(ValueCarrier):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def apply(self):
        return self.value

    def stash(self):
        return self.value


class SingletypeCarrier(PlainCarrier):
    def __init__(self, value_type, prop_value):
        value = {value_type: prop_value}
        super().__init__(value)


class PropertyDecorator(ValueCarrier, metaclass=ABCMeta):
    value_type = 'None'

    def __init__(self, prop_name):
        super().__init__()
        self.prop_name = prop_name

    def apply(self):
        return {
            'type': self.value_type,
            self.value_type: self.stash()
        }


class SingletypeDecorator(PropertyDecorator, DictStash):
    def __init__(self, prop_name, prop_value):
        super().__init__(prop_name)
        self.edit(SingletypeDecorator(self.value_type, prop_value))


class MultitypeDecorator(PropertyDecorator, ListStash):
    def __init__(self, prop_name, prop_values):
        super().__init__(prop_name)
        self.subcarriers = [SingletypeDecorator(self.value_type, value)
                            for value in prop_values]
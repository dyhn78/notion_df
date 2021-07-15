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


class TwofoldStash(ValueCarrier, metaclass=ABCMeta):
    def __init__(self):
        self._subcarriers = []

    def __bool__(self):
        return bool(self._subcarriers)

    def clear(self):
        self._subcarriers = []


class TwofoldListStash(TwofoldStash, metaclass=ABCMeta):
    def _unpack(self):
        return [carrier.apply() for carrier in self._subcarriers]

    def stash(self, carrier: ValueCarrier):
        self._subcarriers.append(carrier)
        return carrier

    def stashleft(self, carrier: ValueCarrier):
        self._subcarriers.insert(0, carrier)
        return carrier


class TwofoldDictStash(TwofoldStash, metaclass=ABCMeta):
    def _unpack(self):
        res = {}
        for carrier in self._subcarriers:
            for key, value in carrier.apply().items():
                res[key] = value
        return res

    def stash(self, carrier: ValueCarrier):
        """
        return 값을 carrier가 아니라 subcarriers[-1]로 설정하였다.
        본래 리스트 append 메소드는 원본 id를 그대로 유지한 채 집어넣어야 정상이지만,
        id 값을 조사해보면 컴퓨터가 carrier의 복사본을 넣는다는 점을 발견할 수 있다.
        """
        self._subcarriers.append(carrier)
        return self._subcarriers[-1]

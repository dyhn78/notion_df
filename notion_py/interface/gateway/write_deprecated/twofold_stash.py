from abc import ABCMeta

from notion_py.interface.struct import ValueCarrier


class TwofoldStash(ValueCarrier, metaclass=ABCMeta):
    def __init__(self):
        self._subcarriers = []

    def __bool__(self):
        return bool(self._subcarriers)

    def clear(self):
        self._subcarriers = []


class TwofoldListStash(TwofoldStash, metaclass=ABCMeta):
    def _unpack(self):
        return [carrier.preview() for carrier in self._subcarriers]

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
            for key, value in carrier.preview().items():
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
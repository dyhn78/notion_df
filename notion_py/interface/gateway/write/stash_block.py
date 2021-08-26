from abc import ABCMeta

from notion_py.interface.struct import TwofoldStash, ValueCarrier


class TwofoldListStash(TwofoldStash, metaclass=ABCMeta):
    def _unwrap(self):
        return [carrier.unpack() for carrier in self._subcarriers]

    def apply_left(self, carrier: ValueCarrier):
        self._subcarriers.insert(0, carrier)
        return self._subcarriers[0]


class BlockChildrenStash(TwofoldListStash):
    def unpack(self):
        return {'children': self._unwrap()}

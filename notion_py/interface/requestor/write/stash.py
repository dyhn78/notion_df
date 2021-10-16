from abc import ABCMeta

from notion_py.interface.common.stash import TwofoldStash
from notion_py.interface.common.struct import ValueCarrier
from notion_py.interface.encoder import ContentsEncoder


class TwofoldListStash(TwofoldStash, metaclass=ABCMeta):
    def unpack(self):
        return [carrier.unpack() for carrier in self._subcarriers]

    def apply_left(self, carrier: ValueCarrier):
        self._subcarriers.insert(0, carrier)
        return self._subcarriers[0]

    def insert(self, i: int, carrier: ValueCarrier):
        self._subcarriers.insert(i, carrier)
        return self._subcarriers[i]


class BlockChildrenStash(ValueCarrier):
    def __init__(self):
        self.block_value = TwofoldListStash()

    def __bool__(self):
        return bool(self.block_value)

    def clear(self):
        self.block_value.clear()

    def unpack(self):
        return {'children': self.block_value.unpack()}

    def apply_contents(self, i: int, carrier: ContentsEncoder):
        return self.block_value.insert(i, carrier)


class TwofoldDictStash(TwofoldStash, metaclass=ABCMeta):
    def unpack(self):
        res = {}
        for carrier in self._subcarriers:
            res.update(**{key: value for key, value in carrier.unpack().items()})
        return res


class PagePropertyStash(ValueCarrier):
    def __init__(self):
        self.prop_value = TwofoldDictStash()

    def __bool__(self):
        return bool(self.prop_value)

    def clear(self):
        self.prop_value.clear()

    def unpack(self) -> dict:
        return {'properties': self.prop_value.unpack()}

    def apply_prop(self, carrier: ValueCarrier):
        return self.prop_value.apply(carrier)


class ArchiveToggle(ValueCarrier):
    def __init__(self):
        self.archive_value = None

    def __bool__(self):
        return self.archive_value is not None

    def is_archived(self):
        return self.archive_value

    def clear(self):
        self.archive_value = None

    def archive(self):
        self.archive_value = True

    def un_archive(self):
        self.archive_value = False

    def unpack(self) -> dict:
        print({'archived': self.archive_value})
        return {'archived': self.archive_value} if bool(self) else {}

from abc import ABCMeta

from notion_py.interface.struct import TwofoldStash, ValueCarrier
from notion_py.interface.api_encode import ContentsEncoder


class TwofoldListStash(TwofoldStash, metaclass=ABCMeta):
    def unpack(self):
        return [carrier.unpack() for carrier in self._subcarriers]

    def apply_left(self, carrier: ValueCarrier):
        self._subcarriers.insert(0, carrier)
        return self._subcarriers[0]


class BlockChildrenStash(ValueCarrier):
    def __init__(self):
        self._block_value = TwofoldListStash()

    def __bool__(self):
        return bool(self._block_value)

    def clear(self):
        self._block_value.clear()

    def unpack(self):
        return {'children': self._block_value.unpack()}

    def apply_contents(self, carrier: ContentsEncoder):
        return self._block_value.apply(carrier)


class TwofoldDictStash(TwofoldStash, metaclass=ABCMeta):
    def unpack(self):
        res = {}
        for carrier in self._subcarriers:
            res.update(**{key: value for key, value in carrier.unpack().items()})
        return res


class PagePropertyStash(ValueCarrier):
    def __init__(self):
        self._prop_value = TwofoldDictStash()

    def __bool__(self):
        return bool(self._prop_value)

    def clear(self):
        self._prop_value.clear()

    def unpack(self) -> dict:
        return {'properties': self._prop_value.unpack()}

    def apply_prop(self, carrier: ValueCarrier):
        return self._prop_value.apply(carrier)


class ArchiveToggle(ValueCarrier):
    def __init__(self):
        self._archive_value = None

    def __bool__(self):
        return self._archive_value is not None

    def clear(self):
        self._archive_value = None

    def archive(self):
        self._archive_value = True

    def un_archive(self):
        self._archive_value = False

    def unpack(self) -> dict:
        return {'archived': self._archive_value} if self else {}

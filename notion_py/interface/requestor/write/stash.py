from abc import ABCMeta

from notion_py.interface.common.stash import TwofoldStash
from notion_py.interface.common.struct import ValueCarrier
from notion_py.interface.encoder import ContentsEncoder


class BlockChildrenStash(ValueCarrier):
    def __init__(self):
        self.subcarriers = []

    def __bool__(self):
        return bool(self.subcarriers)

    def clear(self):
        self.subcarriers.clear()

    def encode(self):
        stash = [carrier.encode() for carrier in self.subcarriers]
        return {'children': stash}

    def apply_contents(self, i: int, carrier: ContentsEncoder):
        self.subcarriers[i] = carrier
        return self.subcarriers[i]

    def append_space(self):
        self.subcarriers.append(None)


class TwofoldDictStash(TwofoldStash, metaclass=ABCMeta):
    def encode(self):
        res = {}
        for carrier in self._subcarriers:
            res.update(**{key: value for key, value in carrier.encode().items()})
        return res


class PagePropertyStash(ValueCarrier):
    def __init__(self):
        self.prop_value = TwofoldDictStash()

    def __bool__(self):
        return bool(self.prop_value)

    def clear(self):
        self.prop_value.clear()

    def encode(self) -> dict:
        return {'properties': self.prop_value.encode()}

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

    def encode(self) -> dict:
        print({'archived': self.archive_value})
        return {'archived': self.archive_value} if bool(self) else {}

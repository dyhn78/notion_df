from abc import ABCMeta

from ...common import TwofoldStash


class TwofoldDictStash(TwofoldStash, metaclass=ABCMeta):
    def _unwrap(self):
        res = {}
        for carrier in self._subcarriers:
            res.update(**{key: value for key, value in carrier.unpack().items()})
        return res


class PagePropertyStash(TwofoldDictStash):
    def unpack(self) -> dict:
        return {'properties': self._unwrap()}

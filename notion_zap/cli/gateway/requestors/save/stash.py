from typing import Optional

from notion_zap.cli.gateway import encoders
from notion_zap.cli.struct.base_classes import ValueCarrier


class BlockChildrenStash(ValueCarrier):
    def __init__(self):
        self.subcarriers: list[Optional[encoders.ContentsEncoder]] = []

    def __bool__(self):
        return bool(self.subcarriers)

    def clear(self):
        self.subcarriers.clear()

    def encode(self):
        stash = [carrier.encode() for carrier in self.subcarriers
                 if carrier is not None]
        return {'children': stash}

    def apply_contents(self, i: int, carrier: encoders.ContentsEncoder) \
            -> encoders.ContentsEncoder:
        while len(self.subcarriers) <= i:
            self.subcarriers.append(None)
        self.subcarriers[i] = carrier
        return self.subcarriers[i]


class PagePropertyStash(ValueCarrier):
    def __init__(self):
        self.subcarriers: list[ValueCarrier] = []
        # self.prop_value = TwofoldDictStash()

    def __bool__(self):
        if not self.subcarriers:
            return False
        return any(bool(carrier) for carrier in self.subcarriers)

    def clear(self):
        self.subcarriers = []
        # self.prop_value.clear()

    def encode(self) -> dict:
        return {'properties': self._unpack()}
        # return {'properties': self.prop_value.encode()}

    def _unpack(self):
        res = {}
        for carrier in self.subcarriers:
            res.update(**{key: value for key, value in carrier.encode().items()})
        return res

    def apply_prop(self, carrier: ValueCarrier):
        """
        return 값을 carrier가 아니라 subcarriers[-1]로 설정하였다.
        본래 리스트 append 메소드는 원본 id를 그대로 유지한 채 집어넣어야 정상이지만,
        id 값을 조사해보면 컴퓨터가 carrier의 복사본을 넣는다는 점을 발견할 수 있다.
        """
        self.subcarriers.append(carrier)
        return self.subcarriers[-1]
        # return self.prop_value.apply(carrier)


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

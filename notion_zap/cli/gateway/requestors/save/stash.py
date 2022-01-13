from typing import Optional

from notion_zap.cli.gateway import encoders
from notion_zap.cli.structs.base_logic import ValueCarrier


class BlockChildrenStash(ValueCarrier):
    def __init__(self):
        self.__carriers: list[Optional[encoders.ContentsEncoder]] = []

    def __bool__(self):
        return bool(self.__carriers)

    def clear(self):
        self.__carriers.clear()

    def encode(self):
        stash = [carrier.encode() for carrier in self.__carriers
                 if carrier is not None]
        return {'children': stash}

    def apply_contents(self, i: int, carrier: encoders.ContentsEncoder) \
            -> encoders.ContentsEncoder:
        while len(self.__carriers) <= i:
            self.__carriers.append(None)
        self.__carriers[i] = carrier
        return self.__carriers[i]


class PagePropertyStash(ValueCarrier):
    def __init__(self):
        self.__carriers: list[ValueCarrier] = []
        # self.prop_value = TwofoldDictStash()

    def __bool__(self):
        if not self.__carriers:
            return False
        return any(bool(carrier) for carrier in self.__carriers)

    def clear(self):
        self.__carriers = []
        # self.prop_value.clear()

    def encode(self) -> dict:
        return {'properties': self._unpack()}
        # return {'properties': self.prop_value.encode()}

    def _unpack(self):
        res = {}
        for carrier in self.__carriers:
            res.update(**{key: value for key, value in carrier.encode().items()})
        return res

    def apply_prop(self, carrier: ValueCarrier):
        """
        return 값을 carrier가 아니라 subcarriers[-1]로 설정하였다.
        본래 리스트 append 메소드는 원본 id를 그대로 유지한 채 집어넣어야 정상이지만,
        id 값을 조사해보면 컴퓨터가 carrier의 복사본을 넣는다는 점을 발견할 수 있다.
        """
        self.__carriers.append(carrier)
        return self.__carriers[-1]
        # return self.prop_value.apply(carrier)


# class ArchiveToggle(ValueCarrier):
#     def __init__(self):
#         self.archive_value = None
#
#     def __bool__(self):
#         return self.archive_value is not None
#
#     def is_archived(self):
#         return self.archive_value
#
#     def clear(self):
#         self.archive_value = None
#
#     def archive(self):
#         self.archive_value = True
#
#     def un_archive(self):
#         self.archive_value = False
#
#     def encode(self) -> dict:
#         return {'archived': self.archive_value} if bool(self) else {}

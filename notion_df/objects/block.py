# 공통 Property는 Block 차원에서 기본으로 정의
# BlockMeta는 Block 딱 하나에서만 상속할 것.
# 용어 정리: "Block" 이라 하면 (Block, PageBlock, PageRow, ...) 를 모두 가리킨다
from __future__ import annotations

from notion_df.core import Entity, MutableField, Field, FieldValueInput_T, FieldValue_T


class BlockIdField(Field['Block', str, str]):
    """real id on the server"""

    def __init__(self):
        super().__init__('')

    @classmethod
    def read_value(cls, _value: FieldValueInput_T) -> FieldValue_T:
        return _value

    ...


class TempIdField(Field):
    """temporary identification for yet-not-created entities"""
    ...


class TitleField(MutableField):
    """available on PageBlock"""
    ...


class ColumnField(MutableField):
    """available on PageRow"""
    ...


class DateColumn(ColumnField):
    ...


class RelationColumn(ColumnField):
    ...


class Block(Entity):
    _id = BlockIdField()
    _temp_id = TempIdField()

    @property
    def pk(self):
        return self._id if self._id else self._temp_id

    @property
    def id(self):
        return self._id


class PageBlock(Block):
    title = TitleField()


class PageItem(PageBlock):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정


class PageRow(PageBlock):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정

# 공통 Property는 Block 차원에서 기본으로 정의
# BlockMeta는 Block 딱 하나에서만 상속할 것.
# 용어 정리: "Block" 이라 하면 (Block, PageBlock, PageRow, ...) 를 모두 가리킨다
from __future__ import annotations

from notion_df.entities.core import Value_T, ValueInput_T, Entity, Field, MutableField, Property


class BlockIdField(Field['Block', str, str]):
    """real id on the server"""

    def __init__(self):
        super().__init__('')

    @classmethod
    def _parse_value(cls, value_input: ValueInput_T) -> Value_T:
        return value_input

    ...


class TempIdField(Field):
    """temporary identification for yet-not-created entity_types"""
    ...


class TitleField(MutableField):
    """available on PageBlock"""
    ...


class ColumnField(MutableField):
    """available on PageRow"""

    def read_property(self, property_input) -> Property:
        ...
        # TODO: type hinting for property_input (also __init__)
        # TODO: self.gen_property(property_input, entity) or self.read_property(property_name) ?


class DateColumn(ColumnField):
    ...


class RelationColumn(ColumnField):
    ...


class Block(Entity):
    id = BlockIdField()
    id_temp = TempIdField()

    @property
    def pk(self):
        return self.id if self.id else self.id_temp


class PageBlock(Block):
    title = TitleField()


class PageItem(PageBlock):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정


class PageRow(PageBlock):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정

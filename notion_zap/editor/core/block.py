from __future__ import annotations

from typing import Type

from notion_zap.editor.core.entity import EntityMeta, BaseProperty, BaseEntity


class BlockId(BaseProperty[str]):
    """real id on the server"""
    ...


class TempId(BaseProperty[str]):
    """temporary identification for yet-not-created blocks"""
    ...


class Title(BaseProperty[str]):
    """available on PageBlock"""
    ...


class Field(BaseProperty):
    """available on PageRow"""
    ...


class DateField(Field):
    ...


class RelationField(Field):
    ...


# 공통 Property는 Block 차원에서 기본으로 정의
# BlockMeta는 BaseBlock 딱 하나에서만 상속할 것.
# 용어 정리: "Block" 이라 하면 (BaseBlock, PageBlock, PageRow, ...) 를 모두 가리킨다
class BaseBlockMeta(EntityMeta):
    pass


class BaseBlock(BaseEntity, metaclass=BaseBlockMeta):
    allowed_property_types: list[Type[BaseProperty]] = []
    id = BlockId()
    temp_id = TempId()

    @property
    def pk(self):
        return self.id if self.id else self.temp_id


class PageBlock(BaseBlock, metaclass=BaseBlockMeta):
    title = Title()


class PageItem(PageBlock, metaclass=EntityMeta):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정


class PageRow(PageBlock, metaclass=EntityMeta):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정

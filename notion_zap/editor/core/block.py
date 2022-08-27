# 공통 Property는 Block 차원에서 기본으로 정의
# BlockMeta는 BaseBlock 딱 하나에서만 상속할 것.
# 용어 정리: "Block" 이라 하면 (BaseBlock, PageBlock, PageRow, ...) 를 모두 가리킨다
from __future__ import annotations

from typing import Type, Any, cast

from notion_zap.editor.core.entity import EntityMeta, BaseField, BaseEntity
from notion_zap.editor.core.utils import NotionZapException


class BaseBlockMeta(EntityMeta):
    def __new__(mcs, name, bases, namespace: dict[str, Any]):
        cls = cast(Type[BaseBlock], type.__new__(mcs, name, bases, namespace))
        for key, value in namespace.items():
            if isinstance(value, BaseField):
                if not any(isinstance(value, allowed_property_type)
                           for allowed_property_type in cls.allowed_property_types):
                    raise PropertyTypeException(name, key, value)
        return cls


class PropertyTypeException(NotionZapException):
    """the block type does not allow this type of property."""

    def __init__(self, block_type_name: str, block_property_name: str, block_property_value: BaseField):
        self.args = (f"{block_type_name}.{block_property_name}: {type(block_property_value).__name__}",)


class BlockId(BaseField[str]):
    """real id on the server"""
    ...


class TempId(BaseField[str]):
    """temporary identification for yet-not-created blocks"""
    ...


class Title(BaseField[str]):
    """available on PageBlock"""
    ...


class PageRowProperty(BaseField):
    """available on PageRow"""
    ...


class DateProperty(PageRowProperty):
    ...


class RelationProperty(PageRowProperty):
    ...


class BaseBlock(BaseEntity, metaclass=BaseBlockMeta):
    allowed_property_types: list[Type[BaseField]] = []  # TODO: delete
    _id = BlockId()
    _temp_id = TempId()

    @property
    def pk(self):
        return self._id if self._id else self._temp_id

    @property
    def id(self):
        return self._id


class PageBlock(BaseBlock, metaclass=BaseBlockMeta):
    title = Title()


class PageItem(PageBlock, metaclass=EntityMeta):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정


class PageRow(PageBlock, metaclass=EntityMeta):
    def __new__(cls): ...  # Field를 사용할 수 있도록 설정

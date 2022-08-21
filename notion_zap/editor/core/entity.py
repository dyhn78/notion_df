from __future__ import annotations

from abc import abstractmethod
from typing import Type, Any, cast, TypeVar, Generic, Optional

from notion_zap.editor.core.utils import NotionZapException


class EntityMeta(type):
    # TODO: ABCMeta.__call__
    def __new__(mcs, name, bases, namespace: dict[str, Any]):
        cls = cast(Type[Entity], type.__new__(mcs, name, bases, namespace))
        for key, value in namespace.items():
            if isinstance(value, BaseProperty):
                if not any(isinstance(value, allowed_property_type)
                           for allowed_property_type in cls.allowed_property_types):
                    raise PropertyTypeException(name, key, value)
        return cls


class BaseEntity(metaclass=EntityMeta):
    @property
    @abstractmethod
    def pk(self) -> str:
        pass


Entity = TypeVar('Entity', bound=BaseEntity)
PropertyValue = TypeVar('PropertyValue')


class BaseProperty(Generic[PropertyValue, Entity]):
    def __init__(self, default_value: Optional[PropertyValue] = None):
        """None default_value means no default value. 
        remind that you cannot actually store null value on Notion."""  # TODO: better documentation
        self.data: dict[Entity, PropertyValue] = {}  # TODO: naming. candidate: 'column', 'spectrum'
        self.default_value: Optional[PropertyValue] = default_value

    def __get__(self, instance: Optional[Entity], owner: Type[Entity]) -> PropertyValue:
        if instance is None:
            return self.default_value
        if self.default_value is None:
            return self.data[instance]
        return self.data.get(instance, self.default_value)

    def __set__(self, instance: Optional[Entity], value: PropertyValue):
        if instance is None:
            self.default_value = value
        else:
            self.data[instance] = value


class PropertyTypeException(NotionZapException):
    """the block type does not allow this type of property."""

    def __init__(self, block_type_name: str, block_property_name: str, block_property_value: BaseProperty):
        self.args = (f"{block_type_name}.{block_property_name}: {type(block_property_value).__name__}",)

from __future__ import annotations

from abc import abstractmethod
from typing import Type, Any, cast, TypeVar, Generic, Optional


class EntityMeta(type):
    # TODO: ABCMeta.__call__
    def __new__(mcs, name, bases, namespace: dict[str, Any]):
        cls = cast(Type[Entity], type.__new__(mcs, name, bases, namespace))
        return cls


class BaseEntity(metaclass=EntityMeta):
    @property
    @abstractmethod
    def pk(self) -> str:
        pass


Entity = TypeVar('Entity', bound=BaseEntity)
FieldValue = TypeVar('FieldValue')


class BaseField(Generic[FieldValue, Entity]):
    def __init__(self, default_value: Optional[FieldValue] = None):
        """None default_value means no default value. 
        remind that you cannot actually store null value on Notion."""  # TODO: better documentation
        self.data: dict[Entity, FieldValue] = {}  # TODO: naming. candidate: 'column', 'spectrum'
        self.default_value: Optional[FieldValue] = default_value

    def __get__(self, instance: Optional[Entity], owner: Type[Entity]) -> FieldValue:
        if instance is None:
            return self.default_value
        if self.default_value is None:
            return self.data[instance]
        return self.data.get(instance, self.default_value)

    def __set__(self, instance: Optional[Entity], value: FieldValue):
        if instance is None:
            self.default_value = value
        else:
            self.data[instance] = value

from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import ClassVar, Any, final

from typing_extensions import Self


class ResourceType(ABCMeta):
    registry: ClassVar[dict[tuple[str, ...], type[Resource]]] = {}

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls: type[Resource] = super().__new__(mcs, name, bases, namespace, **kwargs)  # type: ignore

        import inspect

        signature = inspect.signature(cls.__init__).parameters
        print(cls, signature)

        try:
            self = cls()  # TODO: initiate cls with default values (ex) None, object()
        except TypeError:
            pass
        else:
            full_type = cls.find_type(self.to_dict())
            ResourceType.registry[full_type] = cls
        return cls


@dataclass
class Resource(metaclass=ResourceType):
    """base dataclass used to communicate with Notion API. interchangeable to JSON object."""
    registry: ClassVar[dict[tuple[str, ...], type[Resource]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # self = cls()  # TODO: initiate cls with default values (ex) None, object()
        # full_type = Resource.find_type(self.to_dict())
        # Resource.registry[full_type] = cls

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        """automatically overridden on subclassing"""
        subclass = cls.registry[cls.find_type(d)]
        return subclass.from_dict(d)

    @classmethod
    @final
    def find_type(cls, d: dict) -> tuple[str, ...]:
        full_type = []
        if 'type' not in d:
            raise ValueError(f"'type' not in d :: {d.keys()=}")
        while True:
            key = d['type']
            value = d[key]
            full_type.append(key)
            if isinstance(value, dict) and 'type' in value:
                d = value
                continue
            return tuple(full_type)

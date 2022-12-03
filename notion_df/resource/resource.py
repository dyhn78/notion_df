from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import ClassVar, Any

from typing_extensions import Self


@dataclass
class Resource(metaclass=ABCMeta):
    """base dataclass used to communicate with Notion API. interchangeable to JSON object."""
    registry: ClassVar[dict[tuple[str, ...], type[Resource]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, '__mock__', False):
            return
        type_key_chain = get_type_key_chain(ResourceParser(cls).to_dict)
        Resource.registry[type_key_chain] = cls

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        """automatically overridden on subclassing"""
        subclass = cls.registry[get_type_key_chain(d)]
        return subclass.from_dict(d)


class ResourceParser:
    def __init__(self, resource_cls: type[Resource]):
        class ResourceMock(resource_cls, metaclass=ABCMeta):
            __mock__ = True

            def __init__(self):
                pass

            def __getattr__(self, key: str):
                try:
                    return super().__getattr__(key)  # type: ignore
                except AttributeError:
                    return f'self.{key}'

        self.mock = ResourceMock()
        self.to_dict = self.mock.to_dict()


def get_type_key_chain(d: dict) -> tuple[str, ...]:
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

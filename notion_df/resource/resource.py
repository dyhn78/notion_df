from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import ClassVar, Any

from typing_extensions import Self

from notion_df.util import NotionDfValueError


@dataclass
class Resource(metaclass=ABCMeta):
    """base dataclass used to communicate with Notion API. interchangeable to JSON object."""
    registry: ClassVar[dict[tuple[str, ...], type[Resource]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, '__mock__', False):
            return
        type_key_chain = ResourceDefinitionParser(cls).type_key_chain
        Resource.registry[type_key_chain] = cls

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        """automatically overridden on subclassing"""
        subclass = cls.registry[get_type_key_chain(d)]
        return subclass.from_dict(d)


class ResourceDefinitionParser:
    def __init__(self, resource_cls: type[Resource]):
        class ResourceMock(resource_cls, metaclass=ABCMeta):
            __mock__ = True

            def __init__(self):
                pass

            def __getattr__(self, key: str):
                try:
                    return getattr(super(), key)
                except AttributeError:
                    return AttributeMock(key)

        self.mock_to_dict = ResourceMock().to_dict()
        self.type_key_chain = get_type_key_chain(self.mock_to_dict)

        self.attr_dict: dict[tuple[str, ...], AttributeMock] = {}
        items = [((k,), v) for k, v in self.mock_to_dict.items()]
        while items:
            key_chain, value = items.pop()
            if isinstance(value, AttributeMock):
                if self.attr_dict.get(key_chain) == value:
                    raise NotionDfValueError(f"Resource.to_dict() cannot have value made of multiple attributes")
                self.attr_dict[key_chain] = value
            elif isinstance(value, dict):
                ...  # TODO


@dataclass
class AttributeMock:
    name: str


def get_type_key_chain(d: dict) -> tuple[str, ...]:
    current_key_chain = []
    if 'type' not in d:
        raise NotionDfValueError(f"'type' not in d :: {d.keys()=}")
    while True:
        key = d['type']
        value = d[key]
        current_key_chain.append(key)
        if isinstance(value, dict) and 'type' in value:
            d = value
            continue
        return tuple(current_key_chain)

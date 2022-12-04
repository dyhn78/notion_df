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

    def __init__(self, **kwargs):
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, '__mock__', False):
            return
        parser = ResourceDefinitionParser(cls)
        Resource.registry[parser.type_key_chain] = cls
        cls.from_dict = parser.get_from_dict()

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        """automatically overridden on subclassing"""
        subclass = cls.registry[get_type_key_chain(d)]
        return subclass.from_dict(d)


class ResourceDefinitionParser:
    def __init__(self, origin: type[Resource]):
        self.origin = origin

        class ResourceMock(origin, metaclass=ABCMeta):
            __mock__ = True

            def __getattr__(self, key: str):
                try:
                    return getattr(super(), key)
                except AttributeError:
                    return AttributeMock(key)

        self.mock_to_dict = ResourceMock().to_dict()
        self.type_key_chain = get_type_key_chain(self.mock_to_dict)

        self.attr_dict: dict[tuple[str, ...], AttributeMock] = {}
        items: list[tuple[tuple[str, ...], Any]] = [((k,), v) for k, v in self.mock_to_dict.items()]
        while items:
            key_chain, value = items.pop()
            if isinstance(value, AttributeMock):
                if self.attr_dict.get(key_chain) == value:
                    raise NotionDfValueError(f"Resource.to_dict() cannot have value made of multiple attributes")
                self.attr_dict[key_chain] = value
            elif isinstance(value, dict):
                items.extend((key_chain + (k,), v) for k, v in value.items())

    def get_from_dict(self):
        def from_dict(d: dict):
            kwargs = {}
            for key_chain, attr_name in self.attr_dict.items():
                value = d
                for key in key_chain:
                    value = value[key]
                kwargs[attr_name] = value
            return self.origin(**kwargs)

        return from_dict


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

from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Any, final, ClassVar

from typing_extensions import Self

from notion_df.util import NotionDfValueError


@dataclass
class Resource(metaclass=ABCMeta):
    """base dataclass used to communicate with Notion API. interchangeable to JSON object."""
    _registry: ClassVar[dict[tuple[str, ...], type[Resource]]] = {}
    _attr_name_dict: ClassVar[dict[tuple[str, ...], str]]

    def __init__(self, **kwargs):
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, '__mock__', False):
            return

        class ResourceMock(cls, metaclass=ABCMeta):
            __mock__ = True

            def __getattr__(self, key: str):
                try:
                    return getattr(super(), key)
                except AttributeError:
                    return AttributeMock(key)

        @dataclass
        class AttributeMock:
            name: str

        mock_to_dict = ResourceMock().to_dict()
        Resource._registry[cls._get_type_key_chain(mock_to_dict)] = cls

        cls._attr_name_dict = {}
        items: list[tuple[tuple[str, ...], Any]] = [((k,), v) for k, v in mock_to_dict.items()]
        while items:
            key_chain, value = items.pop()
            if isinstance(value, AttributeMock):
                if cls._attr_name_dict.get(key_chain) == value:
                    raise NotionDfValueError(f"Resource.to_dict() cannot have value made of multiple attributes")
                cls._attr_name_dict[key_chain] = value.name
            elif isinstance(value, dict):
                items.extend((key_chain + (k,), v) for k, v in value.items())

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}

    @classmethod
    @final
    def from_dict(cls, d: dict) -> Self:
        if cls is Resource:
            subclass = cls._registry[cls._get_type_key_chain(d)]
            return subclass.from_dict(d)
        else:
            kwargs = {}
            for key_chain, attr_name in cls._attr_name_dict.items():
                value = d
                for key in key_chain:
                    value = value[key]
                kwargs[attr_name] = value
            return cls(**kwargs)

    @staticmethod
    @final
    def _get_type_key_chain(d: dict) -> tuple[str, ...]:
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

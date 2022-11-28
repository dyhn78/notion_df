from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Final, Any, final

from typing_extensions import Self


class Resource(metaclass=ABCMeta):
    """base dataclass used to communicate with Notion API. interchangeable to JSON object."""
    registry: Final[dict[tuple[str, ...], Self]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        self = cls()  # TODO: initiate cls with default values (ex) None, object()
        full_type = Resource.find_type(self.to_dict())
        Resource.registry[full_type] = cls

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> Self:
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

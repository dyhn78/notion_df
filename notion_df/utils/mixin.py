from abc import ABC, abstractmethod
from typing import Any


class Dictable(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...


# class Dictable2(Dictable):
#     @classmethod
#     @abstractmethod
#     def from_dict(cls, value: dict) -> Self: ...

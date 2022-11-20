from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

_T = TypeVar('_T')


class Dictable(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...


# class Dictable2(Dictable):
#     @classmethod
#     @abstractmethod
#     def from_dict(cls, value: dict) -> Self: ...
class Promise(Generic[_T]):
    @abstractmethod
    def resolve(self) -> _T:
        pass

from abc import abstractmethod
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')


class Promise(Generic[T]):
    @abstractmethod
    def resolve(self) -> T:
        pass


class PromiseProto(Protocol[T]):
    @abstractmethod
    def resolve(self) -> T:
        pass

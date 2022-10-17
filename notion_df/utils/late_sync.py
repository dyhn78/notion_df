from abc import abstractmethod
from typing import TypeVar, Generic, Iterator, Iterable, Mapping

from notion_df.utils.promise import Promise

T = TypeVar('T')
P = TypeVar('P')


class LateSync(Promise[T], Generic[T, P]):
    @classmethod
    @abstractmethod
    def _init(cls) -> T:
        pass

    @abstractmethod
    def _update(self, *args: P) -> None:
        pass

    @abstractmethod
    def _fetch(self) -> Iterator[P]:
        pass

    def __init__(self):
        self.value: T = self._init()
        self._enabled: bool = False

    @property
    def enabled(self):
        return self._enabled

    def resolve(self) -> T:
        if not self.enabled:
            self._enabled = True
            self.update(self._fetch())
        return self.value

    def update(self, items: Iterable[P] | Mapping[P]) -> None:
        if self.enabled:
            if isinstance(items, Mapping):
                items = items.items()
            for item in items:
                self._update(*item)

    def clear(self):
        self.__init__()

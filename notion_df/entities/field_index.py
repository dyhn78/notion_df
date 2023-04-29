from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Final, Mapping, TypeVar, Any, Iterable, Callable

from notion_df.entities.core import Entity_T, Value_T, Field, FieldEventListener
from notion_df.utils.collection import DictView
from notion_df.utils.mixin import Resolvable

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')


class FieldStat(FieldEventListener[Entity_T, Value_T], Resolvable, metaclass=ABCMeta):
    def __init__(self, field: Field[Entity_T, Value_T, Any],
                 generate_init_model: Callable[[], Any]):
        FieldEventListener.__init__(self, field)
        self._generate_init_model: Final = generate_init_model
        self.model: dict[_KT, _VT] = generate_init_model()
        self.view = Final[DictView[_KT, _VT]](self)
        self._enabled: bool = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def resolve(self) -> dict[_KT, _VT]:
        if not self.enabled:
            self._enabled = True
            self.update(self._fetch())
        return self.model

    def update(self, items: Mapping[Entity_T, Value_T] | Iterable[tuple[Entity_T, Value_T]]) -> None:
        if self.enabled:
            if isinstance(items, Mapping):
                items = items.items()
            for item in items:
                self._update_one(*item)

    @abstractmethod
    def _update_one(self, entity: Entity_T, value: Value_T) -> None:
        pass

    def clear(self):
        self.__init__(self.field, self._generate_init_model)


class FieldIndex(FieldStat[Entity_T, Value_T]):
    model: dict[Entity_T, Value_T]

    def __init__(self, field: Field[Entity_T, Value_T, Any]):
        super().__init__(field, lambda: {})

    def _update_one(self, entity: Entity_T, value: Value_T):
        self.model[entity] = value


class FieldInvertedIndexAll(FieldStat[Entity_T, Value_T]):
    model: dict[Value_T, list[Entity_T]]

    def __init__(self, field: Field[Entity_T, Value_T, Any]):
        super().__init__(field, lambda: defaultdict(list))

    def _update_one(self, entity: Entity_T, value: Value_T):
        self.model[value].append(entity)


class FieldInvertedIndexFirst(FieldStat[Entity_T, Value_T]):
    model: dict[Value_T, Entity_T]

    def __init__(self, field: Field[Entity_T, Value_T, Any]):
        super().__init__(field, lambda: {})

    def _update_one(self, entity: Entity_T, value: Value_T):
        self.model.setdefault(value, entity)


class FieldInvertedIndexLast(FieldStat[Entity_T, Value_T]):
    model: dict[Value_T, Entity_T]

    def __init__(self, field: Field[Entity_T, Value_T, Any]):
        super().__init__(field, lambda: {})

    def _update_one(self, entity: Entity_T, value: Value_T):
        self.model[value] = entity

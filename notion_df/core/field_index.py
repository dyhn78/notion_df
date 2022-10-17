from __future__ import annotations

from abc import ABCMeta
from collections import defaultdict
from typing import Final, Mapping, Literal, Iterator, TypeVar, Any, Generic

from notion_df.core import Entity_T, Value_T, Field, FieldEventListener
from notion_df.utils import repr_object
from notion_df.utils.late_sync import LateSync

T = TypeVar('T')


class FieldLateSync(LateSync, FieldEventListener[Entity_T, Value_T], Generic[Entity_T, Value_T], metaclass=ABCMeta):
    def __init__(self, field: Field[Entity_T, Value_T, Any]):
        LateSync.__init__(self)
        FieldEventListener.__init__(self, field)


class IndexModel(FieldLateSync[Entity_T, Value_T], metaclass=ABCMeta):
    @classmethod
    def _init(cls):
        return {}

    def _update(self, entity: Entity_T, value: Value_T):
        self.value[entity] = value

    def resolve(self) -> dict[Entity_T, Value_T]:
        return super().resolve()


class InvertedIndexModel(FieldLateSync[Entity_T, Value_T], metaclass=ABCMeta):
    @classmethod
    def _init(cls):
        return defaultdict(list)

    def _update(self, entity: Entity_T, value: Value_T):
        self.value[value].append(entity)

    def resolve(self) -> dict[Value_T, list[Entity_T]]:
        return super().resolve()


class InvertedIndexUnique(Mapping[Value_T, Entity_T]):
    def __init__(self, _data_input: InvertedIndexModel[Entity_T, Value_T],
                 position: Literal['first', 'last'], field_typename: str):
        self._data_input = _data_input
        self.field_type: Final = field_typename
        self.position: Final = position
        self.position_index: Final = {
            'first': 0, 'last': -1
        }[position]

    @property
    def _data(self) -> dict[Value_T, list[Entity_T]]:
        return self._data_input.resolve()

    def __getitem__(self, field_value: Value_T) -> Entity_T:
        return self._data[field_value][self.position_index]

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> Iterator[Value_T]:
        return self._data.__iter__()

    def __repr__(self) -> str:
        data = {value: self[value] for value in self._data}
        return repr_object(self, field_type=self.field_type, view_type=f'inverted_index_{self.position}', data=data)

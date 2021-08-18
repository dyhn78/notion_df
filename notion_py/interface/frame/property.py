from __future__ import annotations
from typing import Optional, ValuesView, ItemsView, Mapping
from itertools import chain


class PropertyFrame(dict):
    def __init__(self, units: Optional[list[PropertyUnit]] = None):
        super().__init__({})
        if units is not None:
            self.update({unit.name: unit for unit in units})
        self.key_to_name = {}

    def update(self, __m: Mapping[str, PropertyUnit],
               **kwargs: dict[str, PropertyUnit]):
        super().update(__m, **kwargs)
        for prop_name, frame_unit in chain(__m.items(), kwargs.items()):
            self.key_to_name.update({frame_unit.key: prop_name})

    def __getitem__(self, item) -> PropertyUnit:
        return super().__getitem__(item)

    def values(self) -> ValuesView[PropertyUnit]:
        return super().values()

    def items(self) -> ItemsView[str, PropertyUnit]:
        return super().items()


class PropertyUnit:
    def __init__(self, prop_name: str,
                 prop_key: Optional[str] = None,
                 prop_type: Optional[str] = None,
                 prop_values: Optional[dict] = None,
                 prop_value_groups: Optional[dict] = None):
        self.name = prop_name
        self.key = prop_key
        self.type = prop_type
        self.values = prop_values
        self.value_groups = prop_value_groups

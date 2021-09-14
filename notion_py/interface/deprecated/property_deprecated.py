from __future__ import annotations
from typing import Optional, ValuesView, ItemsView


class PropertyFrameDeprecated(dict):
    def __init__(self, values: Optional[dict] = None):
        if values is None:
            values = {}
        super().__init__({key: PropertyUnitDeprecated(value)
                          for key, value in values.items()})

    def __getitem__(self, item) -> PropertyUnitDeprecated:
        return super().__getitem__(item)

    def values(self) -> ValuesView[PropertyUnitDeprecated]:
        return super().values()

    def items(self) -> ItemsView[str, PropertyUnitDeprecated]:
        return super().items()


class PropertyUnitDeprecated:
    def __init__(self, values=None):
        if type(values) == tuple:
            prop_name, prop_values = values
        elif type(values) == str:
            prop_name, prop_values = values, None
        else:
            raise TypeError(f'Invalid PropertyFrameUnit: {values}')
        self.name = prop_name
        self.values = prop_values
        self.type = None

    def set_type(self, value: str):
        self.type = value

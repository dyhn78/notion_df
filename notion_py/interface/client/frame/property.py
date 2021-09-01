from __future__ import annotations
from typing import Optional, Iterable, Union

from ...api_format.parse import PageParser, DatabaseParser


class PropertyFrame:
    def __init__(self, units: Optional[list[PropertyUnit]] = None):
        if units is None:
            units = []
        self.values: list[PropertyUnit] = []
        self.key_to_name: dict[str, str] = {}
        self.by_key: dict[str, PropertyUnit] = {}
        self.by_name: dict[str, PropertyUnit] = {}
        self.extend(units)

    def __iter__(self):
        return self.values

    def __len__(self):
        return len(self.values)

    def __getitem__(self, prop_name: str):
        return self.by_name[prop_name]

    def extend(self, frame_units: Iterable[PropertyUnit]):
        for unit in frame_units:
            self.append(unit)

    def append(self, frame_unit: PropertyUnit):
        self.values.append(frame_unit)
        self.key_to_name.update({frame_unit.key: frame_unit.name})
        self.by_name.update({frame_unit.name: frame_unit})
        self.by_key.update({frame_unit.key: frame_unit})

    def fetch_parser(self, parser: Union[PageParser, DatabaseParser]):
        for prop_name, prop_type in parser.prop_types:
            frame_unit = self.by_name[prop_name]
            frame_unit.type = prop_type


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

from __future__ import annotations
from typing import Optional, Iterable, Union

from ..api_format.parse import PageParser, DatabaseParser


class PropertyUnit:
    def __init__(self, name: str,
                 key: Optional[str] = None,
                 data_type: Optional[str] = None,
                 values: Optional[dict] = None,
                 value_groups_by_name: Optional[dict] = None,
                 value_groups_by_key: Optional[dict] = None,
                 value_infos_by_name: Optional[dict] = None,
                 value_infos_by_key: Optional[dict] = None):
        self.name = name
        self.key = key
        self.data_type = data_type
        self.values = values

        self.value_groups = {}
        if value_groups_by_name:
            self.value_groups.update(**value_groups_by_name)
        if values and value_groups_by_key:
            self.value_groups.update(
                **{value_group_name: [values[key] for key in value_group_by_key]
                   for value_group_name, value_group_by_key
                   in value_groups_by_key.items()
                   })
        self.value_infos = {}
        if value_infos_by_name:
            self.value_infos.update(**value_infos_by_name)
        if values and value_infos_by_key:
            self.value_infos.update(
                **{values[value_key]: value_comment
                   for value_key, value_comment in value_infos_by_key.items()
                   })


class PropertyFrame:
    def __init__(self, units: Optional[list[PropertyUnit]] = None):
        if units is None:
            units = []
        self.values: list[PropertyUnit] = []
        self.key_to_name: dict[str, str] = {}
        self.by_key: dict[str, PropertyUnit] = {}
        self.by_name: dict[str, PropertyUnit] = {}
        self.extend(units)

    def name_at(self, prop_key: str):
        return self.by_key[prop_key].name

    def type_of(self, prop_name: str):
        return self.by_name[prop_name].data_type

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def extend(self, frame_units: Iterable[PropertyUnit]):
        for unit in frame_units:
            self.append(unit)

    def append(self, frame_unit: PropertyUnit):
        self.values.append(frame_unit)
        self.key_to_name.update({frame_unit.key: frame_unit.name})
        self.by_name.update({frame_unit.name: frame_unit})
        self.by_key.update({frame_unit.key: frame_unit})

    def fetch_parser(self, parser: Union[PageParser, DatabaseParser]):
        for name, data_type in parser.prop_types.items():
            if name in self.by_name:
                frame_unit = self.by_name[name]
                frame_unit.data_type = data_type
            else:
                self.append(PropertyUnit(name, data_type=data_type))

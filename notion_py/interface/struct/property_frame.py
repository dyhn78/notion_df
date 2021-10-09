from __future__ import annotations
from typing import Optional, Iterable, Union
from copy import deepcopy

from notion_py.interface.api_parse import PageParser, DatabaseParser


class PropertyFrameUnit:
    def __init__(self, key: str,
                 tag: str = '',
                 data_type: str = '',
                 api_format: str = '',
                 values: Optional[dict] = None,
                 value_groups_by_key: Optional[dict] = None,
                 value_groups_by_tag: Optional[dict] = None,
                 value_infos_by_key: Optional[dict] = None,
                 value_infos_by_tag: Optional[dict] = None):
        self.prop_key = key
        self.prop_tag = tag
        self.prop_type = data_type
        self.prop_foramt = api_format
        self.prop_values = values

        self.prop_value_groups = {}
        if value_groups_by_key:
            self.prop_value_groups.update(**value_groups_by_key)
        if values and value_groups_by_tag:
            self.prop_value_groups.update(
                **{value_group_name: [values[key] for key in value_group_by_key]
                   for value_group_name, value_group_by_key
                   in value_groups_by_tag.items()
                   })
        self.prop_value_infos = {}
        if value_infos_by_key:
            self.prop_value_infos.update(**value_infos_by_key)
        if values and value_infos_by_tag:
            self.prop_value_infos.update(
                **{values[value_key]: value_comment
                   for value_key, value_comment in value_infos_by_tag.items()
                   })

    def __str__(self):
        return f"{self.prop_key} | {self.prop_tag} | {self.prop_type}"


class PropertyFrame:
    def __init__(self,
                 *args: list[Union[PropertyFrameUnit,
                                   list[PropertyFrameUnit],
                                   PropertyFrame]]):
        self.values: list[PropertyFrameUnit] = []
        self.by_key: dict[str, PropertyFrameUnit] = {}
        self.by_name: dict[str, PropertyFrameUnit] = {}
        units = []
        for u in args:
            if isinstance(u, PropertyFrameUnit):
                units.append(u)
            elif isinstance(u, PropertyFrame) or isinstance(u, list):
                for fu in u:
                    units.append(fu)
        self.extend(units)

    def key_at(self, prop_tag: str):
        return self.by_key[prop_tag].prop_key

    def type_of(self, prop_key: str):
        return self.by_name[prop_key].prop_type

    def keys(self):
        return self.by_key.keys()

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __str__(self):
        return "----\n" + '\n'.join([str(unit) for unit in self.values]) + "\n----"

    def extend(self, frame_units: Iterable[PropertyFrameUnit]):
        for unit in frame_units:
            self.append(unit)

    def append(self, frame_unit: PropertyFrameUnit):
        self.values.append(frame_unit)
        self.by_name.update({frame_unit.prop_key: frame_unit})
        if frame_unit.prop_tag:
            self.by_key.update({frame_unit.prop_tag: frame_unit})

    def add_alias(self, original_tag: str, new_tag: str):
        unit = self.by_key[original_tag]
        new_unit = deepcopy(unit)
        new_unit.prop_tag = new_tag
        self.append(new_unit)

    def fetch_parser(self, parser: Union[PageParser, DatabaseParser]):
        for name, data_type in parser.prop_types.items():
            if name in self.by_name:
                frame_unit = self.by_name[name]
                frame_unit.prop_type = data_type
            else:
                self.append(PropertyFrameUnit(name, data_type=data_type))

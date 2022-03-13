from __future__ import annotations

from copy import deepcopy
from typing import Optional, Union, Any, Hashable, Iterable

from notion_zap.cli.gateway import parsers
from notion_zap.cli.structs.prop_types import VALUE_FORMATS


class PropertyValueLabel:
    def __init__(self, value: Any,
                 alias: Hashable,
                 marks: Optional[Iterable[Hashable]] = None):
        self.value = value
        self.alias = alias
        self.marks = marks


class PropertyColumn:
    def __init__(self, key: str,
                 alias: Hashable = None,
                 aliases: Iterable[Hashable] = None,
                 data_type: str = '',
                 labels: Optional[Iterable[PropertyValueLabel]] = None):
        self.data_type = data_type
        self.key = key
        self.key_aliases = []
        if alias is not None:
            assert isinstance(alias, Hashable)
            self.key_aliases.append(alias)
        if aliases is not None:
            for alias in aliases:
                assert isinstance(alias, Hashable)
                self.key_aliases.append(alias)
        self.label_map: dict[Hashable, PropertyValueLabel] \
            = {label.alias: label for label in labels} if labels else {}

    def __str__(self):
        return ' | '.join(
            [self.key, ', '.join(str(tag) for tag in self.key_aliases), self.data_type])

    @property
    def parser_type(self):
        return VALUE_FORMATS[self.data_type]

    def label_of(self, value, default=None):
        for label in self.label_map.values():
            if label.value == value:
                return label
        return default

    def marked_labels(self, mark: Hashable) -> list[PropertyValueLabel]:
        res = []
        for label in self.label_map.values():
            if mark in label.marks:
                res.append(label)
        return res

    def marked_values(self, mark: Hashable):
        res = []
        for label in self.label_map.values():
            if mark in label.marks:
                res.append(label.value)
        return res


class PropertyFrame:
    def __init__(self, *args: Union[PropertyFrame, list[PropertyColumn]]):
        self.units: list[PropertyColumn] = self._flatten(args)
        self.title_key = ''

    @staticmethod
    def _flatten(args):
        res = []
        for arg in args:
            if isinstance(arg, PropertyFrame):
                units = arg.units
            else:
                for a in arg:
                    assert isinstance(a, PropertyColumn)
                units = arg
            res.extend(units)
        return res

    def mapping_of_tag_to_key(self):
        res = {}
        for unit in self.units:
            res.update({tag: unit.key for tag in unit.key_aliases})
        return res

    @property
    def by_key(self):
        res = {}
        for unit in self.units:
            res.update({unit.key: unit})
        return res

    @property
    def by_alias(self) -> dict[Hashable, PropertyColumn]:
        res = {}
        for unit in self.units:
            res.update({key_alias: unit for key_alias in unit.key_aliases})
        return res

    def key_of(self, key_alias: Hashable):
        try:
            return self.by_alias[key_alias].key
        except KeyError:
            raise KeyError(key_alias, self.mapping_of_tag_to_key())

    def type_of(self, prop_key: str):
        return self.by_key[prop_key].data_type

    def keys(self):
        return self.by_key.keys()

    def tags(self):
        return self.by_alias.keys()

    def __iter__(self):
        return iter(self.units)

    def __len__(self):
        return len(self.units)

    def __str__(self):
        return "----\n" + '\n'.join([str(unit) for unit in self.units]) + "\n----"

    def append(self, unit: PropertyColumn):
        self.units.append(unit)

    def add_alias(self, tag: str, new_tag: str):
        unit = self.by_alias[tag]
        new_unit = deepcopy(unit)
        new_unit.tag = new_tag
        self.append(new_unit)

    def assign_title_key(self, key: str):
        self.title_key = key

    def assign_title_tag(self, tag: str):
        self.title_key = self.key_of(tag)

    def fetch_parser(self, parser: Union[parsers.PageParser, parsers.DatabaseParser]):
        for name, data_type in parser.data_types.items():
            if name in self.by_key:
                frame_unit = self.by_key[name]
                frame_unit.data_type = data_type
            else:
                self.append(PropertyColumn(name, data_type=data_type))
        if isinstance(parser, parsers.PageParser):
            self.assign_title_key(parser.pagerow_title_key)

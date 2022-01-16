from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Optional, Union, Any, Hashable

from notion_zap.cli.gateway import parsers
from notion_zap.cli.structs.prop_types import VALUE_FORMATS


class PropertyColumn:
    def __init__(self, key: str,
                 tag: Hashable = None,
                 tags: list[Hashable] = None,
                 data_type: str = '',
                 labels: Optional[dict[Hashable, Any]] = None,
                 marks_on_value: Optional[dict[Hashable, list]] = None,
                 marks_on_label: Optional[dict[Hashable, list]] = None):
        self.key = key
        self.data_type = data_type

        self.tags = tags if tags is not None else []
        if tag is not None:
            self.tags.append(tag)
        self.labels = labels if labels is not None else {}
        self._value_to_label = {value: key for key, value in self.labels.items()}

        self.marks = {}
        if marks_on_value:
            self.marks.update(**marks_on_value)
        if self.labels and marks_on_label:
            for mark, marked_labels in marks_on_label.items():
                values = [self.labels[label] for label in marked_labels]
                self.marks.update({mark: values})
        self._value_to_mark = defaultdict(list)
        for mark, values in self.marks.items():
            for value in values:
                self._value_to_mark[value].append(mark)

    def __str__(self):
        return ' | '.join(
            [self.key, ', '.join(str(tag) for tag in self.tags), self.data_type])

    @property
    def parser_type(self):
        return VALUE_FORMATS[self.data_type]

    def label_of(self, value, default=None):
        return self._value_to_label.get(value, default)

    def marks_of(self, value, default=None):
        if default is None:
            default = []
        return self._value_to_mark.get(value, default)


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
            res.update({tag: unit.key for tag in unit.tags})
        return res

    @property
    def by_key(self):
        res = {}
        for unit in self.units:
            res.update({unit.key: unit})
        return res

    @property
    def by_tag(self) -> dict[Hashable, PropertyColumn]:
        res = {}
        for unit in self.units:
            res.update({tag: unit for tag in unit.tags})
        return res

    def key_of(self, prop_tag: Hashable):
        try:
            return self.by_tag[prop_tag].key
        except KeyError:
            raise KeyError(prop_tag, self.mapping_of_tag_to_key())

    def type_of(self, prop_key: str):
        return self.by_key[prop_key].data_type

    def keys(self):
        return self.by_key.keys()

    def tags(self):
        return self.by_tag.keys()

    def __iter__(self):
        return iter(self.units)

    def __len__(self):
        return len(self.units)

    def __str__(self):
        return "----\n" + '\n'.join([str(unit) for unit in self.units]) + "\n----"

    def append(self, unit: PropertyColumn):
        self.units.append(unit)

    def add_alias(self, tag: str, new_tag: str):
        unit = self.by_tag[tag]
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

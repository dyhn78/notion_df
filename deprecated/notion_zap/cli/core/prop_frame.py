from __future__ import annotations

from typing import Optional, Union, Any, Hashable, Iterable

from notion_zap.cli.core.prop_types import VALUE_FORMATS
from notion_zap.cli.gateway import parsers


# TODO: Enum 적용
class PropertyMarkedValue:
    def __init__(self, value: Any,
                 alias: Hashable,
                 tags: Optional[Iterable[Hashable]] = None):
        self.value = value
        self.alias = alias
        self.tags: list[Hashable] = list(tags) if tags else []

    def __str__(self):
        return f"marked_value({self.value}, alias= {self.alias}, tags= {self.tags})"


# TODO: Enum 적용
class PropertyColumn:
    def __init__(self, key: str,
                 alias: Hashable = None,
                 aliases: Iterable[Hashable] = None,
                 data_type: str = '',
                 marked_values: Optional[Iterable[PropertyMarkedValue]] = None):
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
        self.marks: dict[Hashable, PropertyMarkedValue] \
            = {mark.alias: mark for mark in marked_values} if marked_values else {}

    def __str__(self):
        return ' | '.join(
            [self.key, ', '.join(str(tag) for tag in self.key_aliases), self.data_type])

    @property
    def parser_type(self):
        return VALUE_FORMATS[self.data_type]

    def coalesce_mark(self, *value_or_aliases):
        for value_or_alias in value_or_aliases:
            for mark in self.marks.values():
                if value_or_alias in [mark.value, mark.alias]:
                    return mark
        raise KeyError(f"{value_or_aliases=}, {self.marks=}")

    def get_mark_by_value(self, value):
        for mark in self.marks.values():
            if mark.value == value:
                return mark
        raise KeyError

    def get_mark_by_alias(self, alias):
        for mark in self.marks.values():
            if mark.alias == alias:
                return mark
        raise KeyError

    def filter_marks(self, tag: Hashable) -> list[PropertyMarkedValue]:
        res = []
        for mark in self.marks.values():
            if tag in mark.tags:
                res.append(mark)
        return res

    def filter_values(self, tag: Hashable):
        res = []
        for mark in self.marks.values():
            if tag in mark.tags:
                res.append(mark.value)
        return res


class PropertyFrame:
    def __init__(self, *args: Union[PropertyFrame, list[PropertyColumn]]):
        self.columns: list[PropertyColumn] = self._flatten(args)
        self.title_key = ''

    @staticmethod
    def _flatten(args):
        res = []
        for arg in args:
            if isinstance(arg, PropertyFrame):
                units = arg.columns
            else:
                for a in arg:
                    assert isinstance(a, PropertyColumn)
                units = arg
            res.extend(units)
        return res

    def mapping_of_tag_to_key(self):
        res = {}
        for unit in self.columns:
            res.update({tag: unit.key for tag in unit.key_aliases})
        return res

    @property
    def by_key(self):
        res = {}
        for cl in self.columns:
            res.update({cl.key: cl})
        return res

    @property
    def by_alias(self) -> dict[Hashable, PropertyColumn]:
        res = {}
        for cl in self.columns:
            res.update({key_alias: cl for key_alias in cl.key_aliases})
        return res

    def get_key(self, key_alias: Hashable):
        try:
            return self.by_alias[key_alias].key
        except KeyError:
            raise KeyError(key_alias, self.mapping_of_tag_to_key())

    def get_type(self, prop_key: str):
        return self.by_key[prop_key].data_type

    def keys(self):
        return self.by_key.keys()

    def key_aliases(self):
        return self.by_alias.keys()

    def __iter__(self):
        return iter(self.columns)

    def __len__(self):
        return len(self.columns)

    def __str__(self):
        return "----\n" + '\n'.join([str(unit) for unit in self.columns]) + "\n----"

    def append(self, unit: PropertyColumn):
        self.columns.append(unit)

    def assign_title_key(self, key: str):
        self.title_key = key

    def fetch_parser(self, parser: Union[parsers.PageParser, parsers.DatabaseParser]):
        for name, data_type in parser.data_types.items():
            if name in self.by_key:
                frame_unit = self.by_key[name]
                frame_unit.data_type = data_type
            else:
                self.append(PropertyColumn(name, data_type=data_type))
        if isinstance(parser, parsers.PageParser):
            self.assign_title_key(parser.pagerow_title_key)

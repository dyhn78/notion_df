from __future__ import annotations
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Union, Optional, Hashable

from notion_zap.cli.structs import PropertyFrame
from ..common.page import PageBlock
from ..common.with_children import Children
from ..structs.leaders import Root, Registerer


class PageRow(PageBlock):
    def __init__(self, caller: Union[Root, Children],
                 id_or_url: str,
                 frame: Optional[PropertyFrame] = None):
        from ..database.leaders import RowChildren
        super().__init__(caller, id_or_url)
        self.caller: Union[Root, RowChildren] = caller
        self.frame = frame if frame else PropertyFrame()

        from .props import PageRowProperties
        self.props = PageRowProperties(self, id_or_url)

        self.regs_key: dict[str, PropertyRegisterer] = dict(self.caller.key_tables)
        self.regs_tag: dict[str, PropertyRegisterer] = {}

    @property
    def parent(self):
        from ..database.leaders import Database
        if parent := self.parent:
            assert isinstance(parent, Database)
            return parent
        return None

    @property
    def payload(self):
        return self.props

    @property
    def regs(self):
        return [self.reg_id, self.reg_title,
                *self.regs_key.values(), *self.regs_tag.values()]

    @property
    def regs_prop(self) -> dict[str, PropertyRegisterer]:
        return {**self.regs_key, **self.regs_tag}


class PropertyRegisterer(Registerer, metaclass=ABCMeta):
    def __init__(self, caller: PageRow,
                 parents_table: Union[IndexTable, ClassifyTable],
                 roots_table: Union[IndexTable, ClassifyTable]):
        super().__init__(caller)
        self.caller = caller
        self.parents_table = parents_table
        self.roots_table = roots_table

    @property
    def block(self) -> PageRow:
        return self.caller

    @property
    @abstractmethod
    def idx(self):
        pass

    def register_to_parent(self):
        self.parents_table.update({self.idx: self.block})

    def register_to_root_and_parent(self):
        self.register_to_parent()
        self.roots_table.update({self.idx: self.block})

    def un_register_from_parent(self):
        self.parents_table.remove({self.idx: self.block})

    def un_register_from_root_and_parent(self):
        self.un_register_from_parent()
        self.roots_table.remove({self.idx: self.block})


class IndexKeyRegisterer(PropertyRegisterer):
    def __init__(self, caller: PageRow, prop_key: str):
        self.prop_key = prop_key
        self.parents_table = self.caller.caller.key_tables[self.prop_key]
        self.roots_table = self.root.key_tables[self.prop_key]
        super().__init__(caller, self.parents_table, self.roots_table)

    @property
    def idx(self):
        return self.block.props.read_key(self.prop_key)


class ClassifyKeyRegisterer(PropertyRegisterer):
    def __init__(self, caller: PageRow, prop_key: str):
        self.prop_key = prop_key
        self.parents_table = self.caller.caller.tag_tables[self.prop_key]
        self.roots_table = self.root.tag_tables[self.prop_key]
        super().__init__(caller, self.parents_table, self.roots_table)

    @property
    def idx(self):
        return self.block.props.read_key(self.prop_key)


class IndexTagRegisterer(PropertyRegisterer):
    def __init__(self, caller: PageRow, prop_tag: str):
        self.prop_tag = prop_tag
        self.parents_table = self.caller.caller.key_tables[self.prop_tag]
        self.roots_table = self.root.key_tables[self.prop_tag]
        super().__init__(caller, self.parents_table, self.roots_table)

    @property
    def idx(self):
        return self.block.props.read_tag(self.prop_tag)


class ClassifyTagRegisterer(PropertyRegisterer):
    def __init__(self, caller: PageRow, prop_tag: str):
        self.prop_tag = prop_tag
        self.parents_table = self.caller.caller.tag_tables[self.prop_tag]
        self.roots_table = self.root.tag_tables[self.prop_tag]
        super().__init__(caller, self.parents_table, self.roots_table)

    @property
    def idx(self):
        return self.block.props.read_tag(self.prop_tag)


class CacheTable:
    @property
    @abstractmethod
    def table(self):
        pass

    def update(self, mapping: dict[Hashable, PageRow]):
        pass

    def remove(self, mapping: dict[Hashable, PageRow]):
        pass


class IndexTable(CacheTable):
    def __init__(self):
        self._table = {}

    @property
    def table(self) -> dict[Hashable, PageRow]:
        return self._table

    def __getitem__(self, item: Hashable):
        return self._table[item]

    def update(self, mapping: dict[Hashable, PageRow]):
        self._table.update(mapping)

    def remove(self, mapping: dict[Hashable, PageRow]):
        for key, value in mapping:
            if self.table[key] == value:
                self.table.pop(key)


class ClassifyTable(CacheTable):
    def __init__(self):
        self._table = defaultdict(list)

    @property
    def table(self) -> dict[Hashable, list[PageRow]]:
        return self._table

    def update(self, mapping: dict[Hashable, PageRow]):
        for key, value in mapping:
            self._table[key].append(value)

    def remove(self, mapping: dict[Hashable, PageRow]):
        for key, value in mapping:
            if value in self._table[key]:
                self._table[key].remove(value)

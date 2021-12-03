from abc import ABCMeta, abstractmethod
from typing import Hashable

from .main import PageRow, PageRowProperties
from ..structs.registry_table import RegistryTable
from ..structs.registry_writer import Registerer


class PropertyRegisterer(Registerer, metaclass=ABCMeta):
    @property
    def block(self) -> PageRow:
        ret = super().block
        assert isinstance(ret, PageRow)
        return ret

    @property
    @abstractmethod
    def parents_table(self) -> RegistryTable:
        pass

    @property
    @abstractmethod
    def roots_table(self) -> RegistryTable:
        pass

    def register_to_parent(self):
        if self.track_val:
            self.parents_table.update({self.track_val: self.block})

    def register_to_root_and_parent(self):
        self.register_to_parent()
        if self.track_val:
            self.roots_table.update({self.track_val: self.block})

    def un_register_from_parent(self):
        if self.track_val:
            self.parents_table.remove({self.track_val: self.block})

    def un_register_from_root_and_parent(self):
        self.un_register_from_parent()
        if self.track_val:
            self.roots_table.remove({self.track_val: self.block})


class KeyRegisterer(PropertyRegisterer):
    def __init__(self, caller: PageRowProperties, prop_key: str):
        super().__init__(caller)
        self.prop_key = prop_key

    @property
    def track_key(self):
        return 'key', self.prop_key

    @property
    def track_val(self):
        return self.block.props.get_key(self.prop_key)

    @property
    def parents_table(self):
        return self.block.caller.by_keys[self.prop_key]

    @property
    def roots_table(self):
        return self.root.by_keys[self.prop_key]


class TagRegisterer(PropertyRegisterer):
    def __init__(self, caller: PageRowProperties, prop_tag: Hashable):
        self.prop_tag = prop_tag
        super().__init__(caller)

    @property
    def track_key(self):
        return 'tag', self.prop_tag

    @property
    def track_val(self):
        return self.block.props.get_tag(self.prop_tag)

    @property
    def parents_table(self):
        return self.parent.rows.by_tags[self.prop_tag]

    @property
    def roots_table(self):
        return self.root.by_tags[self.prop_tag]

from __future__ import annotations

from enum import Enum
from typing import Iterable, Literal


class Label:
    def __init__(self, superlabels: Iterable[Label]):
        self.superlabels: set[Label] = set()
        for superlabel in superlabels:
            self._recursively_add_superlabels(superlabel)

    def _recursively_add_superlabels(self, superlabel: Label):
        if superlabel in self.superlabels:
            return
        self.superlabels.add(superlabel)
        for super_superlabel in superlabel.superlabels:
            self._recursively_add_superlabels(super_superlabel)


_label_to_label_enum_dict: dict[Label, LabelEnum] = {}


class LabelEnum(Enum):
    def __init__(self, superlabels: Iterable[Label] | Literal[0]):
        if superlabels == 0:
            superlabels = []
        self._value_ = Label(superlabels)
        _label_to_label_enum_dict[self.value] = self

    @property
    def value(self) -> Label:
        return super().value()

    @property
    def super_enums(self) -> set[LabelEnum]:
        return {_label_to_label_enum_dict[label] for label in self.value.superlabels}

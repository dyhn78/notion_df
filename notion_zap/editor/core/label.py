from __future__ import annotations

import logging
from enum import Enum
from typing import Iterable, Optional


class Label:
    # TODO: change "supers" arg to "Self" after python 3.11
    def __init__(self, *superlabels: Label | Iterable[Label]):
        superlabel_values = self._parse_superlabel_input(superlabels)
        logging.debug(f"{self=}, {superlabels=}, {superlabel_values=}")

        self.supers: set[Label] = set()
        for superlabel in superlabel_values:
            self._recursively_add_superlabels(superlabel)

        self.key: Optional[LabelKey] = None

    def _recursively_add_superlabels(self, superlabel: Label):
        if superlabel in self.supers:
            return
        self.supers.add(superlabel)
        for super_superlabel in superlabel.supers:
            self._recursively_add_superlabels(super_superlabel)

    def _parse_superlabel_input(self, superlabel_input: tuple[Label | Iterable[Label]]) -> Iterable[Label]:
        def is_labels_iterable(elements) -> Optional[list[Label]]:
            _labels = []
            for element in elements:
                if isinstance(element, Label):
                    _labels.append(element)
                else:
                    return None
            return _labels

        if (labels := is_labels_iterable(superlabel_input)) is not None:
            return labels
        if len(superlabel_input) == 1 and (labels := is_labels_iterable(superlabel_input[0])) is not None:
            return labels
        raise ValueError(f"{self=}, {superlabel_input=}")


class LabelKey(Enum):
    def __init__(self, value: Label):
        self._value_ = value
        if value.key is not None:
            raise ValueError(f"{self=}, {value=}")
        value.key = self

    def __str__(self):
        args = [self.name]
        if supers := self.supers:
            args.append(f"supers={', '.join(sorted(superkey.name for superkey in supers))}")
        return f"{type(self).__name__}({', '.join(args)})"

    @property
    def value(self) -> Label:
        return self._value_

    @property
    def supers(self) -> set[LabelKey]:
        return {value.key for value in self.value.supers if value.key is not None}

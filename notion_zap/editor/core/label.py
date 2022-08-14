from __future__ import annotations

import logging
from enum import Enum
from typing import Iterable, Optional

from notion_zap.editor.core.helpers import repr_object


class Label:
    # TODO: change "supers" arg to "Self" after python 3.11
    def __init__(self, *superlabels: Label | LabelEnum | tuple[(Label | LabelEnum), ...]):
        superlabel_inputs = superlabels
        superlabels: Iterable[Label] = self._parse_superlabel_input(superlabels)
        logging.debug(f"{self=}, {superlabel_inputs=}, {superlabels=}")

        self.supers: set[Label] = set()
        for superlabel in superlabels:
            self._recursively_add_superlabels(superlabel)

        self.enum: Optional[LabelEnum] = None

    def _recursively_add_superlabels(self, superlabel: Label):
        if superlabel in self.supers:
            return
        self.supers.add(superlabel)
        for super_superlabel in superlabel.supers:
            self._recursively_add_superlabels(super_superlabel)

    def _parse_superlabel_input(
            self, superlabel_inputs: tuple[Label | LabelEnum | tuple[(Label | LabelEnum), ...]]) -> Iterable[Label]:
        def get_from_label_or_label_enum(arg: Label | LabelEnum):
            if isinstance(label_ := arg, Label):
                return label_
            if isinstance(label_enum := arg, LabelEnum):
                return label_enum.value
            return None

        for superlabel_input in superlabel_inputs:
            if (label := get_from_label_or_label_enum(superlabel_input)) is not None:
                yield label
            elif isinstance(superlabel_input, tuple) and \
                    (label := get_from_label_or_label_enum(superlabel_input[0])) is not None:
                yield label
            else:
                raise ValueError(f"{self=}, {superlabel_inputs=}")


class LabelEnum(Enum):
    def __init__(self, value: Label):
        if not (isinstance(value, Label) and value.enum is None):
            raise ValueError(f"{self=}, {value=}")
        self._value_ = value
        value.enum = self

    def __str__(self):
        args = [self.name]
        if supers := self.supers:
            args.append(f"supers={', '.join(sorted(superkey.name for superkey in supers))}")
        return repr_object(self, args)

    @property
    def value(self) -> Label:
        return self._value_

    @property
    def supers(self) -> set[LabelEnum]:
        return {value.enum for value in self.value.supers if value.enum is not None}

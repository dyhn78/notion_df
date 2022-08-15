from __future__ import annotations

import logging
from enum import Enum
from typing import Iterable

from notion_zap.editor.core.helpers import repr_object


class Label:
    # TODO: change "supers" arg to "Self" after python 3.11
    def __init__(self, *supers: Label | LabelEnum | tuple[(Label | LabelEnum), ...]):
        supers_input = supers
        supers: Iterable[Label] = self._parse_super_label_input(supers)
        logging.debug(f"{self=}, {supers_input=}, {supers=}")

        self.supers: set[Label] = set()
        for super_label in supers:
            self._recursively_add_supers(super_label)
        self._enum = None

    @property
    def enum(self) -> LabelEnum | None:
        return self._enum

    @enum.setter
    def enum(self, value: LabelEnum):
        if self.enum is not None:
            raise ValueError(str(self.enum), f"new_value={str(value)}")
        self._enum = value

    def _recursively_add_supers(self, super_label: Label):
        if super_label in self.supers:
            return
        self.supers.add(super_label)
        for super_super_label in super_label.supers:
            self._recursively_add_supers(super_super_label)

    def _parse_super_label_input(
            self, supers_input: tuple[Label | LabelEnum | tuple[(Label | LabelEnum), ...]]) -> Iterable[Label] | None:
        def get_from_label_or_label_enum(arg: Label | LabelEnum):
            if isinstance(label_ := arg, Label):
                return label_
            if isinstance(label_enum := arg, LabelEnum):
                return label_enum.value
            return None

        for super_label_input in supers_input:
            if (label := get_from_label_or_label_enum(super_label_input)) is not None:
                yield label
            elif isinstance(super_label_input, tuple) and \
                    (label := get_from_label_or_label_enum(super_label_input[0])) is not None:
                yield label
            else:
                raise ValueError(f"{self=}, {supers_input=}")


class LabelEnum(Enum):
    def __init__(self, value: Label):
        if not isinstance(value, Label):
            raise ValueError(f"{self=}, {value=}")
        self._value_ = value
        value.enum = self

    def __str__(self):
        args = [self.name]
        if supers := self.supers:
            args.append(f"supers={', '.join(sorted(super_enum.name for super_enum in supers))}")
        return repr_object(self, args)

    @property
    def value(self) -> Label:
        return self._value_

    @property
    def supers(self) -> set[LabelEnum]:
        return {value.enum for value in self.value.supers if value.enum is not None}

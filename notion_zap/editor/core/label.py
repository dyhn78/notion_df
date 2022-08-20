from __future__ import annotations

import logging
from abc import ABCMeta
from collections import defaultdict
from enum import Enum
from typing import Iterable

from notion_zap.editor.core.core_utils import repr_object

_super_members_dict: dict[Label, set[Label]] = defaultdict(set)
_super_names_dict: dict[Label, list[str]] = {}


class Label(Enum, metaclass=ABCMeta):
    @property
    def supers(self):
        return _super_members_dict[self]

    def __init__(self, supers: list[str]):
        self._value_ = self.name
        _super_names_dict[self] = supers

    @classmethod
    def _update_super_members(cls, label: Label):
        super_names = _super_names_dict[label]
        direct_super_members = [cls[super_name] for super_name in super_names]
        super_members = {}
        # TODO
        #  업데이트 중에 자기 자신이 발견되면 "Circular hierarchy" 던지기
        _super_members_dict[label] = super_members

    def __init_subclass__(cls):
        super.__init_subclass__()
        for label in cls:
            cls._update_super_members(label)


class LabelDepr:
    # TODO: change "supers" arg to "Self" after python 3.11
    def __init__(self, *supers: LabelDepr | LabelEnum | tuple[(LabelDepr | LabelEnum), ...]):
        supers_input = supers
        supers: Iterable[LabelDepr] = self._parse_super_label_input(supers)
        logging.debug(f"{self=}, {supers_input=}, {supers=}")

        self.supers: set[LabelDepr] = set()
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

    def _recursively_add_supers(self, super_label: LabelDepr):
        if super_label in self.supers:
            return
        self.supers.add(super_label)
        for super_super_label in super_label.supers:
            self._recursively_add_supers(super_super_label)

    def _parse_super_label_input(
            self, supers_input: tuple[LabelDepr | LabelEnum | tuple[(LabelDepr | LabelEnum), ...]]) -> Iterable[
                                                                                                           LabelDepr] | None:
        def get_from_label_or_label_enum(arg: LabelDepr | LabelEnum):
            if isinstance(label_ := arg, LabelDepr):
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
    def __init__(self, value: LabelDepr):
        if not isinstance(value, LabelDepr):
            raise ValueError(f"{self=}, {value=}")
        self._value_ = value
        value.enum = self

    def __str__(self):
        args = [self.name]
        if supers := self.supers:
            args.append(f"supers={', '.join(sorted(super_enum.name for super_enum in supers))}")
        return repr_object(self, args)

    @property
    def value(self) -> LabelDepr:
        return self._value_

    @property
    def supers(self) -> set[LabelEnum]:
        return {value.enum for value in self.value.supers if value.enum is not None}

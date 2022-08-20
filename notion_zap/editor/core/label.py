from __future__ import annotations

import logging
from enum import Enum
from typing import Iterable, Literal

from notion_zap.editor.core.core_utils import repr_object
from notion_zap.editor.core.exceptions import CircularLabelException

_frozen_super_members_dict: dict[Label, frozenset[Label]] = {}
_direct_super_names_dict: dict[Label, Iterable[str]] = {}


class Label(Enum):
    """to use, create a subclass"""

    @property
    def supers(self) -> frozenset[Label]:
        return _frozen_super_members_dict[self]

    def __init__(self, *supers_input: str | Literal[0, None, '']):
        self._value_ = self.name
        supers = self._cast_supers_input(supers_input)
        _direct_super_names_dict[self] = supers
        logging.debug(f"\t\t{self=}, {supers=}")

    @staticmethod
    def _cast_supers_input(supers: Iterable[str | Literal[0, None, '']]) -> Iterable[str]:
        if all(supers):
            return supers
        return []

    @classmethod
    def _update_super_members(cls, label: Label) -> frozenset[Label]:
        if frozen_super_members := _frozen_super_members_dict.get(label):
            return frozen_super_members

        direct_super_names = _direct_super_names_dict[label]
        super_members = set()
        for direct_super_name in direct_super_names:
            direct_super_member = cls[direct_super_name]
            super_members.add(direct_super_member)

            indirect_super_members = cls._update_super_members(direct_super_member)
            super_members.update(indirect_super_members)

        if label in super_members:
            raise CircularLabelException(f"{cls=}, {label=}")

        frozen_super_members = frozenset(super_members)
        _frozen_super_members_dict[label] = frozen_super_members
        return frozen_super_members

    def __init_subclass__(cls):
        logging.debug(f"Label.__init_subclass__({cls})")
        super.__init_subclass__()
        print(cls)  # TODO : this seems like not triggered at all. consider using debugger.
        for label in cls:
            print(label)
            cls._update_super_members(label)
        logging.debug(f"\t{cls=}, {[f'{label.supers=}' for label in cls]}")

    def __str__(self):
        args = [self.name]
        if supers := self.supers:
            args.append(f"supers={sorted(super_enum.name for super_enum in supers)}")
        return repr_object(self, args)

from __future__ import annotations

import logging
from enum import Enum
from typing import Iterable, Literal

from notion_zap.editor.core.utils import repr_object

_super_names_input = str | Literal[0, None, '']


class Label(Enum):
    """to use, create a subclass"""

    @property
    def supers(self) -> frozenset[Label]:
        return self._supers

    def __init__(self, *super_names: _super_names_input):
        self._value_ = self.name

        super_members = set()
        direct_super_names = self._read_super_names(super_names)
        for direct_super_name in direct_super_names:
            direct_super_member = type(self)[direct_super_name]
            super_members.add(direct_super_member)
            super_members.update(direct_super_member.supers)

        self._supers = frozenset(super_members)
        logging.debug(f"{self=}, {direct_super_names=}, {self._supers=}")

    @staticmethod
    def _read_super_names(super_names: Iterable[_super_names_input]) -> Iterable[str]:
        if all(super_names):
            return super_names
        return []

    def __str__(self):
        args = {'name': self.name}
        if supers := self.supers:
            args['supers'] = sorted(super_enum.name for super_enum in supers)
        return repr_object(self, args)

from __future__ import annotations

from abc import ABCMeta

from ...core.base import Block


class Document(Block, metaclass=ABCMeta):
    @classmethod
    def migrate(cls, block: Document):
        """rebuild the block's structure. used to move a block to heterogeneous parent.
        currently unavailable until the official API supports moving block."""
        pass

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Iterator, Union, Iterable

from .struct import BlockEditor, MasterEditor, Editor


class ChildrenBearer(MasterEditor):
    @abstractmethod
    def __init__(self, caller: Union[BlockEditor, Editor]):
        super().__init__(caller)

    @property
    def is_supported_type(self) -> bool:
        return True

    @property
    @abstractmethod
    def children(self) -> BlockChildren:
        pass

    def iter_descendants_with(self, exact_rank_diff: int) \
            -> Iterable[Union[ChildrenBearer, MasterEditor]]:
        if exact_rank_diff > 0:
            yield from self.__iter_descendants_with(self, exact_rank_diff)
        else:
            return iter([])

    @classmethod
    def __iter_descendants_with(cls, block: ChildrenBearer, exact_rank_diff: int):
        if exact_rank_diff == 0:
            yield block
        else:
            for child in block.children:
                if isinstance(child, ChildrenBearer):
                    yield from cls.__iter_descendants_with(child, exact_rank_diff - 1)

    def iter_descendants_within(self, max_rank_diff: int) \
            -> Iterable[Union[ChildrenBearer, MasterEditor]]:
        if max_rank_diff > 0:
            yield from self.__iter_descendants_within(self, max_rank_diff)
        else:
            return iter([])

    @classmethod
    def __iter_descendants_within(cls, block: ChildrenBearer, max_rank_diff: int):
        if max_rank_diff >= 0:
            yield block
        if max_rank_diff > 0:
            for child in block.children:
                if isinstance(child, ChildrenBearer):
                    yield from cls.__iter_descendants_within(child, max_rank_diff - 1)

    def iter_descendants(self) \
            -> Iterable[Union[ChildrenBearer, MasterEditor]]:
        for child in self.children:
            yield child
            if isinstance(child, ChildrenBearer):
                yield from child.iter_descendants()

    def fetch_descendants_within(self, max_rank_diff: int, min_rank_diff=1,
                                 request_size=0):
        if max_rank_diff <= 0:
            return
        if min_rank_diff - 1 <= 0:
            self.children.fetch(request_size)
        for child in self.children:
            if isinstance(child, ChildrenBearer):
                child.fetch_descendants_within(max_rank_diff - 1, min_rank_diff - 1)

    def fetch_descendants(self, request_size=0):
        self.children.fetch(request_size)
        for child in self.children:
            if isinstance(child, ChildrenBearer):
                child.fetch_descendants(request_size)


class BlockChildren(BlockEditor, metaclass=ABCMeta):
    def __init__(self, caller: ChildrenBearer):
        super().__init__(caller)
        self.caller = caller

    @property
    @abstractmethod
    def by_id(self) -> dict[str, MasterEditor]:
        # will be auto-updated by child blocks.
        pass

    def ids(self):
        return self.by_id.keys()

    @property
    @abstractmethod
    def by_title(self) -> dict[str, list[MasterEditor]]:
        # will be auto-updated by child blocks.
        pass

    def __iter__(self):
        """this will return ALL child blocks, even if
        block.yet_not_created or block.archived."""
        return self.iter_all()

    @abstractmethod
    def iter_all(self) -> Iterator[MasterEditor]:
        pass

    def iter_valids(self, exclude_archived_blocks=True,
                    exclude_yet_not_created_blocks=True) \
            -> Iterator[MasterEditor]:
        for child in self.iter_all():
            if exclude_archived_blocks and child.archived:
                continue
            if exclude_yet_not_created_blocks and child.yet_not_created:
                continue
            yield child

    @abstractmethod
    def fetch(self, request_size=0):
        pass

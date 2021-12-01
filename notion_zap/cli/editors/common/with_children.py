from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Iterator, Union, Iterable

from ..structs.leaders import Block, Registry
from ..structs.followers import Follower


class ChildrenBearer(Block):
    @property
    @abstractmethod
    def children(self) -> BlockChildren:
        pass

    def read(self):
        return dict(**self.basic_info,
                    **self.payload.read(),
                    **self.children.read())

    def richly_read(self):
        return dict(**self.basic_info,
                    **self.payload.richly_read(),
                    **self.children.richly_read())

    def save_info(self):
        return dict(**self.basic_info,
                    **self.payload.save_info(),
                    **self.children.save_info())

    def save_required(self) -> bool:
        return (self.payload.save_required()
                or self.children.save_required())

    @abstractmethod
    def _fetch_children(self, request_size=0):
        pass

    def iter_descendants_with(self, exact_rank_diff: int) \
            -> Iterable[Union[ChildrenBearer, Block]]:
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
            -> Iterable[Union[ChildrenBearer, Block]]:
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
            -> Iterable[Union[ChildrenBearer, Block]]:
        for child in self.children:
            yield child
            if isinstance(child, ChildrenBearer):
                yield from child.iter_descendants()

    def fetch_descendants_within(self, max_rank_diff: int, min_rank_diff=1,
                                 request_size=0):
        if max_rank_diff <= 0:
            return
        if min_rank_diff - 1 <= 0:
            self._fetch_children(request_size)
        for child in self.children:
            if isinstance(child, ChildrenBearer):
                child.fetch_descendants_within(max_rank_diff - 1, min_rank_diff - 1)

    def fetch_descendants(self, request_size=0):
        self._fetch_children(request_size)
        for child in self.children:
            if isinstance(child, ChildrenBearer):
                child.fetch_descendants(request_size)

    @property
    def is_supported_type(self) -> bool:
        return True


class BlockChildren(Follower, Registry, metaclass=ABCMeta):
    def __init__(self, caller: ChildrenBearer):
        Follower.__init__(self, caller)
        Registry.__init__(self)
        self.caller = caller
        self._by_id = {}
        self._by_title = defaultdict(list)

    @abstractmethod
    def list_all(self) -> list[Block]:
        pass

    def iter_all(self) -> Iterator[Block]:
        return iter(self.iter_all())

    def __iter__(self):
        """this will return ALL child blocks, even if
        block.yet_not_created or block.archived."""
        return self.iter_all()

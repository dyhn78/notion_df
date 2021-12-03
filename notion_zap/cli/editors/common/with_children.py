from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Union, Iterable, Any

from ..structs.block_main import Block, Follower
from ..structs.base_logic import Gatherer


class BlockWithChildren(Block, metaclass=ABCMeta):
    @property
    @abstractmethod
    def children(self) -> Children:
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
            -> Iterable[Union[BlockWithChildren, Block]]:
        if exact_rank_diff > 0:
            yield from self.__iter_descendants_with(self, exact_rank_diff)
        else:
            return iter([])

    @classmethod
    def __iter_descendants_with(cls, block: BlockWithChildren, exact_rank_diff: int):
        if exact_rank_diff == 0:
            yield block
        else:
            for child in block.children:
                if isinstance(child, BlockWithChildren):
                    yield from cls.__iter_descendants_with(child, exact_rank_diff - 1)

    def iter_descendants_within(self, max_rank_diff: int) \
            -> Iterable[Union[BlockWithChildren, Block]]:
        if max_rank_diff > 0:
            yield from self.__iter_descendants_within(self, max_rank_diff)
        else:
            return iter([])

    @classmethod
    def __iter_descendants_within(cls, block: BlockWithChildren, max_rank_diff: int):
        if max_rank_diff >= 0:
            yield block
        if max_rank_diff > 0:
            for child in block.children:
                if isinstance(child, BlockWithChildren):
                    yield from cls.__iter_descendants_within(child, max_rank_diff - 1)

    def iter_descendants(self) \
            -> Iterable[Union[BlockWithChildren, Block]]:
        for child in self.children:
            yield child
            if isinstance(child, BlockWithChildren):
                yield from child.iter_descendants()

    def fetch_descendants_within(self, max_rank_diff: int, min_rank_diff=1,
                                 request_size=0):
        if max_rank_diff <= 0:
            return
        if min_rank_diff - 1 <= 0:
            self._fetch_children(request_size)
        for child in self.children:
            if isinstance(child, BlockWithChildren):
                child.fetch_descendants_within(max_rank_diff - 1, min_rank_diff - 1)

    def fetch_descendants(self, request_size=0):
        self._fetch_children(request_size)
        for child in self.children:
            if isinstance(child, BlockWithChildren):
                child.fetch_descendants(request_size)

    @property
    def is_supported_type(self) -> bool:
        return True


class Children(Follower, Gatherer, metaclass=ABCMeta):
    def __init__(self, caller: BlockWithChildren):
        Follower.__init__(self, caller)
        Gatherer.__init__(self)
        self.caller = caller

    @abstractmethod
    def list_all(self) -> list[Block]:
        pass

    def __iter__(self):
        """this will return ALL child blocks on the editor at the moment,
         even yet-not-created or archived ones."""
        return iter(self.list_all())

    def read(self) -> dict[str, Any]:
        return {'children': [child.read() for child in self.list_all()]}

    def richly_read(self) -> dict[str, Any]:
        return {'children': [child.richly_read() for child in self.list_all()]}

    def save_info(self):
        return {'children': [child.save_info() for child in self.list_all()]}

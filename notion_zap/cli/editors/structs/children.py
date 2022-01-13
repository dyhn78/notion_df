from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Union, Iterable, Any

from notion_zap.cli.editors.structs.block_main import Block, Follower
from notion_zap.cli.editors.structs.base_logic import Gatherer
from notion_zap.cli.gateway.requestors.structs import Requestor


class BlockWithChildren(Block, metaclass=ABCMeta):
    @property
    @abstractmethod
    def children(self) -> Children:
        pass

    @property
    def is_supported_type(self) -> bool:
        return True

    def read(self, max_rank_diff=0):
        res = super().read(max_rank_diff)
        if max_rank_diff > 0:
            res.update(**self.children.read(max_rank_diff - 1))
        return res

    def richly_read(self, max_rank_diff=0):
        res = super().richly_read(max_rank_diff)
        if max_rank_diff > 0:
            res.update(**self.children.richly_read(max_rank_diff - 1))
        return res

    def save(self):
        if not (self.is_archived and self.root.exclude_archived):
            self.children.save()
        return self

    def save_info(self):
        return dict(**self.basic_info,
                    **self.children.save_info())

    def save_required(self) -> bool:
        return self.children.save_required()

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

    def iter_all_descendants(self) \
            -> Iterable[Union[BlockWithChildren, Block]]:
        for child in self.children:
            yield child
            if isinstance(child, BlockWithChildren):
                yield from child.iter_all_descendants()

    def fetch_descendants_within(self, max_rank_diff: int, min_rank_diff=1,
                                 request_size=0):
        if max_rank_diff <= 0:
            return
        if min_rank_diff - 1 <= 0:
            self._fetch_children(request_size)
        for child in self.children:
            if isinstance(child, BlockWithChildren):
                child.fetch_descendants_within(max_rank_diff - 1, min_rank_diff - 1)

    def fetch_all_descendants(self, request_size=0):
        self._fetch_children(request_size)
        for child in self.children:
            if isinstance(child, BlockWithChildren):
                child.fetch_all_descendants(request_size)


class BlockWithContentsAndChildren(BlockWithChildren):
    @property
    @abstractmethod
    def requestor(self) -> Requestor:
        pass

    def save(self):
        self._save_this()
        if not (self.is_archived and self.root.exclude_archived):
            self.children.save()
        return self

    @abstractmethod
    def _save_this(self):
        return self.requestor.execute()

    def save_info(self):
        return dict(**self.basic_info,
                    **self._save_this_info(),
                    **self.children.save_info())

    def _save_this_info(self):
        encode: dict = self.requestor.encode()
        return {key: value for key, value in encode.items()
                if key != 'children' and value != self.block_id}

    def save_required(self) -> bool:
        save_this_required = self.requestor.__bool__()
        return (save_this_required()
                or self.children.save_required())


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

    def read(self, max_rank_diff=0) -> dict[str, Any]:
        return {'children': [child.read(max_rank_diff) for child in self.list_all()]}

    def richly_read(self, max_rank_diff=0) -> dict[str, Any]:
        return {'children': [child.richly_read(max_rank_diff)
                             for child in self.list_all()]}

    def save_info(self):
        return {'children': [child.save_info() for child in self.list_all()]}

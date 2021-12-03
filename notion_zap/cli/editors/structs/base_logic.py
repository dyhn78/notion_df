from __future__ import annotations
import os
from abc import ABCMeta, abstractmethod
from pprint import pprint
from typing import Any, Optional, Hashable

from notion_client import AsyncClient, Client

from notion_zap.cli.structs import DateObject, PropertyFrame


class BaseComponent(metaclass=ABCMeta):
    @property
    @abstractmethod
    def root(self) -> Root:
        pass


class Readable:
    @abstractmethod
    def read(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def richly_read(self) -> dict[str, Any]:
        pass


class Saveable(metaclass=ABCMeta):
    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def save_info(self):
        pass

    @abstractmethod
    def save_required(self) -> bool:
        pass

    def save_preview(self, **kwargs):
        pprint(self.save_info(), **kwargs)


from .registry_table import RegistryTable, IndexTable, ClassifyTable


class Registry(BaseComponent, metaclass=ABCMeta):
    def __init__(self):
        from .block_main import Block
        from ..row.main import PageRow
        self.__by_id: IndexTable[str, Block] = IndexTable()
        self.__by_title: ClassifyTable[str, Block] = ClassifyTable()
        self.__by_keys: dict[str, RegistryTable[Hashable, PageRow]] = {}
        self.__by_tags: dict[Hashable, RegistryTable[Hashable, PageRow]] = {}

    @property
    def by_id(self):
        """this will be maintained from childrens' side."""
        return self.__by_id

    def ids(self):
        return self.by_id.keys()

    @property
    def by_title(self):
        """this will be maintained from childrens' side."""
        return self.__by_title

    @property
    def by_keys(self):
        return self.__by_keys

    @property
    def by_tags(self):
        return self.__by_tags


class Root(Registry):
    def __init__(
            self,
            async_client=False,
            exclude_archived=False,
            disable_overwrite=False,
            customized_emptylike_strings=None,
            # enable_overwrite_by_same_value=False,
    ):
        super().__init__()
        if async_client:
            client = AsyncClient(auth=self.token)
        else:
            client = Client(auth=self.token)
        self.client = client

        self.objects = RootGatherer(self)

        from .block_main import Block
        self._blocks: list[Block] = []

        from ..database.main import Database
        self._by_alias: dict[Any, Database] = {}

        # global settings, will be applied uniformly to all child-editors.
        self.exclude_archived = exclude_archived
        self.disable_overwrite = disable_overwrite
        if customized_emptylike_strings is None:
            customized_emptylike_strings = \
                ['', '.', '-', '0', '1', 'None', 'False', '[]', '{}']
        self.emptylike_strings = customized_emptylike_strings
        # self.enable_overwrite_by_same_value = enable_overwrite_by_same_value

        # TODO : (1) enum 이용, (2) 실제로 requestor에 작동하는 로직 마련.
        self._log_succeed_request = False
        self._log_failed_request = True

    @property
    def token(self):
        return os.environ['NOTION_TOKEN'].strip("'").strip('"')

    def count_as_empty(self, value):
        if isinstance(value, DateObject):
            return value.is_emptylike()
        return str(value) in self.emptylike_strings

    def set_logging__silent(self):
        self._log_succeed_request = False
        self._log_failed_request = False

    def set_logging__error(self):
        self._log_succeed_request = False
        self._log_failed_request = True

    def set_logging__all(self):
        self._log_succeed_request = True
        self._log_failed_request = True

    @property
    def root(self):
        return self

    @property
    def by_alias(self):
        return self._by_alias

    @property
    def aliased_blocks(self):
        return self._by_alias.values()

    def save(self):
        return self.objects.save()


class Gatherer(Readable, Saveable, Registry, metaclass=ABCMeta):
    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def attach(self, block):
        """this will be called from child's side."""
        pass

    @abstractmethod
    def detach(self, block):
        """this will be called from child's side."""
        pass


class RootGatherer(Gatherer):
    def __init__(self, caller: Root):
        super().__init__()
        self.caller = caller

        from .block_main import Block
        self.direct_blocks: list[Block] = []

    def __iter__(self):
        return iter(self.direct_blocks)

    @property
    def root(self) -> Root:
        return self.caller

    def save(self):
        for block in self.direct_blocks:
            block.save()

    def save_info(self):
        return [block.save_info() for block in self.direct_blocks]

    def save_required(self):
        return any([block.save_required() for block in self.direct_blocks])

    def read(self) -> dict[str, Any]:
        return {'root': child.read() for child in self.direct_blocks}

    def richly_read(self) -> dict[str, Any]:
        return {'root': child.richly_read() for child in self.direct_blocks}

    def attach(self, block):
        self.direct_blocks.append(block)

    def detach(self, block):
        self.direct_blocks.remove(block)

    def database(self, database_alias: str, id_or_url: str,
                 frame: Optional[PropertyFrame] = None):
        from .. import Database
        block = Database(self, id_or_url, database_alias, frame)
        return block

    def page_row(self, id_or_url: str,
                 frame: Optional[PropertyFrame] = None):
        from .. import PageRow
        block = PageRow(self, id_or_url, frame=frame)
        return block

    def page_item(self, id_or_url: str):
        from .. import PageItem
        block = PageItem(self, id_or_url)
        return block

    def text_item(self, id_or_url: str):
        from .. import TextItem
        block = TextItem(self, id_or_url)
        return block

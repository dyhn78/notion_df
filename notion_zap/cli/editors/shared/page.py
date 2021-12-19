from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Union

from .document import Document
from .with_items import BlockWithItems
from ..structs.base_logic import Gatherer
from ..structs.block_main import Payload
from ..structs.registerer import Registerer
from ..structs.save_agents import RequestEditor
from notion_zap.cli.gateway import parsers, requestors


class PageBlock(BlockWithItems, Document, RequestEditor, metaclass=ABCMeta):
    def __init__(self, caller: Gatherer, id_or_url: str):
        super().__init__(caller, id_or_url)
        self._title = ''
        self.regs.add('title', lambda x: x.block.title)

    @property
    def payload(self) -> PagePayload:
        # noinspection PyTypeChecker
        return super().payload

    @property
    def can_have_children(self):
        return True

    @property
    def block_name(self):
        return self.title

    @property
    def title(self):
        return self._title

    @property
    @abstractmethod
    def requestor(self) -> Union[requestors.CreatePage, requestors.UpdatePage]:
        pass

    @abstractmethod
    def clear_requestor(self):
        pass

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()

    def retrieve(self):
        requestor = requestors.RetrievePage(self)
        response = requestor.execute_silent()
        parser = parsers.PageParser.parse_retrieve_resp(response)
        self.apply_page_parser(parser)
        requestor.print_comments()

    def apply_page_parser(self, parser: parsers.PageParser):
        self.regs.un_register_from_root_and_parent()
        self._apply_page_parser(parser)
        self.regs.register_to_root_and_parent()

    @abstractmethod
    def _apply_page_parser(self, parser: parsers.PageParser):
        self._block_id = parser.page_id
        self._archived = parser.archived
        self._created_time = parser.created_time
        self._last_edited_time = parser.last_edited_time

    def save(self):
        if self.block_id:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update PageParser yourself without response
        else:
            response = self.requestor.execute()
            parser = parsers.PageParser.parse_create_resp(response)
            self.apply_page_parser(parser)
        self.clear_requestor()
        if not (self.archived and self.root.exclude_archived):
            self.children.save()
        return self


class PagePayload(Payload, RequestEditor, metaclass=ABCMeta):
    def __init__(self, caller: PageBlock, block_id: str):
        Payload.__init__(self, caller, block_id)
        self.caller = caller
        self._title = ''
        self.regs.add('title', lambda x: x.block.title)

    @property
    def block(self) -> PageBlock:
        return self.caller

    @property
    @abstractmethod
    def requestor(self) -> Union[requestors.CreatePage, requestors.UpdatePage]:
        pass

    @abstractmethod
    def clear_requestor(self):
        pass

    @property
    def title(self):
        return self._title

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()

    def retrieve(self):
        requestor = requestors.RetrievePage(self)
        response = requestor.execute_silent()
        parser = parsers.PageParser.parse_retrieve_resp(response)
        self.apply_page_parser(parser)
        requestor.print_comments()

    def apply_page_parser(self, parser: parsers.PageParser):
        self.regs.un_register_from_root_and_parent()
        self._apply_page_parser(parser)
        self.regs.register_to_root_and_parent()

    @abstractmethod
    def _apply_page_parser(self, parser: parsers.PageParser):
        self._block_id = parser.page_id
        self._archived = parser.archived
        self._created_time = parser.created_time
        self._last_edited_time = parser.last_edited_time

    def save(self):
        if self.block_id:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update PageParser yourself without response
        else:
            response = self.requestor.execute()
            parser = parsers.PageParser.parse_create_resp(response)
            self.apply_page_parser(parser)
        self.clear_requestor()

    @property
    def can_have_children(self):
        return True


class TitleRegisterer(Registerer):
    @property
    def block(self) -> PageBlock:
        # noinspection PyTypeChecker
        return super().block

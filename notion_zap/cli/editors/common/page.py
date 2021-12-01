from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Union

from .with_items import ItemsBearer
from ..structs.exceptions import DanglingBlockError
from ..structs.leaders import Payload
from ..structs.followers import RequestEditor
from notion_zap.cli.gateway import parsers, requestors


class PageBlock(ItemsBearer):
    @property
    @abstractmethod
    def payload(self) -> PagePayload:
        pass

    @property
    def block_name(self):
        return self.title

    @property
    def title(self):
        return self.payload.title

    def _unregister_from_root(self):
        super()._unregister_from_root()
        if self.title:
            try:
                self.root.search_by_title[self.title].remove(self.title)
            except KeyError:
                raise DanglingBlockError(self, self.root)


class PagePayload(Payload, RequestEditor, metaclass=ABCMeta):
    def __init__(self, caller: PageBlock):
        Payload.__init__(self, caller)
        self.caller = caller
        self.__title = ''

    @property
    @abstractmethod
    def requestor(self) -> Union[requestors.CreatePage, requestors.UpdatePage]:
        pass

    @abstractmethod
    def clear_requestor(self):
        pass

    @property
    def title(self):
        return self.__title

    def _set_title(self, value: str):
        """set the value to empty string('') will unregister the block."""
        if self.__title:
            try:
                self.caller.caller.by_title[self.title].remove(self.block)
            except ValueError:
                raise DanglingBlockError(self.block, self.caller.caller)
            try:
                self.root.search_by_title[self.title].remove(self.block)
            except ValueError:
                raise DanglingBlockError(self.block, self.root)
        self.__title = value
        if self.__title:
            self.caller.caller.by_title[self.title].append(self.block)
            self.root.search_by_title[self.title].append(self.block)

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
        self._set_block_id(parser.page_id)
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

from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Union

from .with_items import ItemsBearer
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


class PagePayload(Payload, RequestEditor, metaclass=ABCMeta):
    def __init__(self, caller: PageBlock, id_or_url):
        Payload.__init__(self, caller, id_or_url)
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
            for attachments in self.register_points:
                try:
                    attachments.by_title[self.__title].remove(self.master)
                except ValueError:
                    print(f'WARNING: {self.master} was not registered to {attachments}')
        self.__title = value
        if self.__title:
            for attachments in self.register_points:
                attachments.by_title[self.__title].append(self.master)

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()

    def apply_page_parser(self, parser: parsers.PageParser):
        if parser.page_id != '':
            self._set_block_id(parser.page_id)
        self._archived = parser.archived
        self._created_time = parser.created_time
        self._last_edited_time = parser.last_edited_time

    def retrieve(self):
        requestor = requestors.RetrievePage(self)
        response = requestor.execute_silent()
        parser = parsers.PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)
        requestor.print_comments()

    def save(self):
        if self.block_id:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update PageParser yourself without response
        else:
            response = self.requestor.execute()
            parser = parsers.PageParser.parse_create(response)
            self.apply_page_parser(parser)
        self.clear_requestor()

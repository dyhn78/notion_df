from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Union

from .with_items import ItemsBearer
from ..base import BlockPayload, GroundEditor
from notion_zap.cli.gateway import parsers, requestors


class PageBlock(ItemsBearer):
    @property
    @abstractmethod
    def payload(self) -> PagePayload:
        pass

    def save_required(self):
        return (self.payload.save_required()
                or self.items.save_required())

    @property
    def block_name(self):
        return self.title

    @property
    def title(self):
        return self.payload.title


class PagePayload(BlockPayload, GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: PageBlock, id_or_url):
        BlockPayload.__init__(self, caller, id_or_url)
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
        self._unregister_title()
        self.__title = value
        self._register_title()

    def _register_title(self):
        if self.title == '':
            return
        # register to root
        register_point = self.root.by_title
        register_point[self.title].append(self.master)
        # register to parent
        if self.parent:
            register_point = self.parent.children.by_title
            register_point[self.title].append(self.master)

    def _unregister_title(self):
        if self.title == '':
            return
        # detach from root
        register_point = self.root.by_title
        register_point[self.title].remove(self.master)
        # detach from parent
        if self.parent:
            register_point = self.parent.children.by_title
            register_point[self.title].remove(self.master)

    def unregister_all(self):
        self._unregister_id()
        self._unregister_title()

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
        if self.yet_not_created:
            response = self.requestor.execute()
            parser = parsers.PageParser.parse_create(response)
            self.apply_page_parser(parser)
        else:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update PageParser yourself without response
        self.clear_requestor()

from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Union

from .document import Document
from .with_items import ItemsBearer
from ..structs.exceptions import DanglingBlockError
from ..structs.leaders import Payload, Registry, Registerer
from ..structs.followers import RequestEditor
from notion_zap.cli.gateway import parsers, requestors


class PageBlock(ItemsBearer, Document):
    def __init__(self, caller: Registry, id_or_url: str):
        super().__init__(caller, id_or_url)
        self.reg_title = TitleRegisterer(self)
        # since title value is empty at this moment
        #  (Payload is not yet initialized),
        #  there's no points to 'register' it.
        #  same thing applies to PageRow,
        #  which doesn't register its initial property value.

    @property
    def regs(self):
        return [self.reg_id, self.reg_title]

    @property
    @abstractmethod
    def payload(self) -> PagePayload:
        pass

    @property
    def block_name(self):
        return self.title

    @property
    def title(self):
        try:
            return self.payload.title
        except AttributeError:
            # this happens during __init__;
            #  reg_title asks to
            #  payload is initialized from implemented class,
            return ''

    def save(self):
        self.payload.save()
        if not self.archived:
            self.children.save()
        return self


class TitleRegisterer(Registerer):
    def __init__(self, caller: PageBlock):
        super().__init__(caller)
        self.caller = caller

    @property
    def block(self) -> PageBlock:
        return self.caller

    @property
    def title(self):
        return self.caller.title

    def register_to_parent(self):
        if self.title:
            self.block.caller.by_title[self.title].append(self.block)

    def register_to_root_and_parent(self):
        self.register_to_parent()
        if self.title:
            self.root.title_table[self.title].append(self.block)

    def un_register_from_parent(self):
        if self.title:
            try:
                self.block.caller.by_title[self.title].remove(self.block)
            except ValueError:
                raise DanglingBlockError(self.block, self.block.caller)

    def un_register_from_root_and_parent(self):
        if self.title:
            try:
                self.root.title_table[self.title].remove(self.block)
            except ValueError:
                raise DanglingBlockError(self.block, self.root)


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
    def block(self) -> PageBlock:
        return self.caller

    @property
    def title(self):
        return self.__title

    def _set_title(self, value: str):
        self.block.reg_title.un_register_from_root_and_parent()
        self.__title = value
        self.block.reg_title.register_to_root_and_parent()

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

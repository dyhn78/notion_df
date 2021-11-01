from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Union

from notion_py.interface.parser import PageParser
from notion_py.interface.requestor import CreatePage, UpdatePage, RetrievePage
from .struct import PointEditor, GroundEditor
from .with_items import ItemsBearer
from ..root_editor import RootEditor


class PageBlock(ItemsBearer):
    def __init__(self, caller: Union[RootEditor, PointEditor],
                 page_id: str,
                 yet_not_created=False):
        super().__init__(caller, page_id)
        self.caller = caller
        self.yet_not_created = yet_not_created
        self._title = ''

    @property
    @abstractmethod
    def payload(self) -> PagePayload:
        pass

    def save_required(self):
        return (self.payload.save_required()
                or self.attachments.save_required())

    @property
    def master_name(self):
        return self.title

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value: str):
        old_value = self.title
        self._title = value

        # register to root
        register_point = self.root.by_title
        if old_value:
            register_point[old_value].remove(self)
        if value:
            register_point[value].append(self)

        # register to parent
        if self.parent:
            register_point = self.parent.children.by_title
            if old_value:
                register_point[old_value].remove(self)
            if value:
                register_point[value].append(self)


class PagePayload(GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: PageBlock):
        super().__init__(caller)
        self.caller = caller

    @property
    @abstractmethod
    def requestor(self) -> Union[CreatePage, UpdatePage]:
        pass

    @requestor.setter
    @abstractmethod
    def requestor(self, value):
        pass

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()

    def retrieve(self):
        requestor = RetrievePage(self)
        response = requestor.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def save(self):
        if self.yet_not_created:
            response = self.requestor.execute()
            parser = PageParser.parse_create(response)
            self.apply_page_parser(parser)
        else:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update PageParser yourself without response
        self.requestor = UpdatePage(self)

    def apply_page_parser(self, parser: PageParser):
        if parser.page_id:
            self.master_id = parser.page_id
            self.yet_not_created = False
        self.caller.title = parser.title
        self.archived = parser.archived

from abc import ABCMeta, abstractmethod
from typing import Union

from .struct import GroundEditor
from ..common.struct import drop_empty_request
from ..parser import PageParser
from ..requestor import CreatePage, UpdatePage, RetrievePage


class PageProperty(GroundEditor, metaclass=ABCMeta):
    @property
    @abstractmethod
    def gateway(self) -> Union[CreatePage, UpdatePage]:
        pass

    @gateway.setter
    @abstractmethod
    def gateway(self, value):
        pass

    def archive(self):
        self.gateway.archive()

    def un_archive(self):
        self.gateway.un_archive()

    def retrieve(self):
        requestor = RetrievePage(self)
        response = requestor.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    @drop_empty_request
    def execute(self):
        if self.yet_not_created:
            response = self.gateway.execute()
            parser = PageParser.parse_create(response)
            self.apply_page_parser(parser)
        else:
            self.gateway.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update PageParser yourself without response
        self.gateway = UpdatePage(self)

    def apply_page_parser(self, parser: PageParser):
        if parser.page_id:
            self.master_id = parser.page_id
            self.yet_not_created = False
        self.master.title = parser.title
        self.archived = parser.archived

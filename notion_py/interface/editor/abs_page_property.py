from abc import ABCMeta, abstractmethod
from typing import Union

from .struct import GroundEditor
from ..parser import PageParser
from ..requestor import CreatePage, UpdatePage, RetrievePage


class PageProperty(GroundEditor, metaclass=ABCMeta):
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

    def execute(self):
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
        self.master.title = parser.title
        self.archived = parser.archived

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Iterable, Any, final

from loguru import logger

from notion_df.entity import Page
from notion_df.util.misc import repr_object
from workflow.block_enum import exclude_template


class Action(metaclass=ABCMeta):
    def __repr__(self) -> str:
        return repr_object(self)

    @final
    def process_all(self) -> Any:
        """query and process"""
        logger.info(self)
        return self._process_all()

    @abstractmethod
    def _process_all(self) -> Any:
        pass

    @final
    def process_pages(self, pages: Iterable[Page]) -> Any:
        """process the given pages"""
        logger.info(self)
        return self._process_pages(pages)

    @abstractmethod
    def _process_pages(self, pages: Iterable[Page]) -> Any:
        pass


class CompositeAction(Action):
    @abstractmethod
    def __init__(self, actions: list[Action]):
        self.actions = actions

    def _process_all(self) -> Any:
        for action in self.actions:
            action._process_all()

    def _process_pages(self, pages: Iterable[Page]) -> Any:
        for action in self.actions:
            action._process_pages(pages)


class IndividualAction(Action):
    def __repr__(self):
        return repr_object(self)

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        setattr(cls, cls.query.__name__, exclude_template(cls.query))

    @final
    def _process_all(self) -> Any:
        return self._process_pages(self.query())

    @abstractmethod
    def query(self) -> Iterable[Page]:
        pass

    @abstractmethod
    def _process_pages(self, pages: Iterable[Page]) -> Any:
        pass


class SequentialAction(IndividualAction):
    @final
    def _process_pages(self, pages: Iterable[Page]) -> Any:
        for page in pages:
            self.process_page(page)

    @abstractmethod
    def process_page(self, page: Page) -> Any:
        pass

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import wraps
from typing import Iterable, Any, final

from loguru import logger

from notion_df.entity import Page
from notion_df.util.misc import repr_object
from workflow.block_enum import exclude_template


class Action(metaclass=ABCMeta):
    def __repr__(self) -> str:
        return repr_object(self)

    def __init_subclass__(cls, **kwargs) -> None:
        process_prev = cls.process

        @wraps(process_prev)
        def process_new(self: Action, pages: Iterable[Page]):
            logger.info(self)
            return process_prev(self, pages)

        setattr(cls, cls.process.__name__, process_new)

    @abstractmethod
    def execute_all(self) -> Any:
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]) -> Any:
        pass


class IndividualAction(Action, metaclass=ABCMeta):
    def __repr__(self):
        return repr_object(self)

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        setattr(cls, cls.query.__name__, exclude_template(cls.query))

    @final
    def execute_all(self) -> Any:
        return self.process(self.query())

    @abstractmethod
    def query(self) -> Iterable[Page]:
        """full-scan mode"""
        pass

    @abstractmethod
    def process(self, pages: Iterable[Page]) -> Any:
        pass


class SequentialAction(IndividualAction, metaclass=ABCMeta):
    @final
    def process(self, pages: Iterable[Page]):
        for page in pages:
            self.process_page(page)

    @abstractmethod
    def process_page(self, page: Page) -> Any:
        pass

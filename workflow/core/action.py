from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from functools import wraps
from pprint import pformat
from typing import Iterable, Any, final, Optional, ParamSpec, Callable

from loguru import logger

from notion_df.entity import Page, search_by_title
from notion_df.util.misc import repr_object
from notion_df.variable import print_width
from workflow import log_dir
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


# TODO: integrate into Action
@exclude_template
def search_pages_by_last_edited_time(lower_bound: datetime, upper_bound: Optional[datetime] = None) -> Iterable[Page]:
    """Note: Notion APIs' last_edited_time info is only with minutes resolution"""
    # TODO: integrate with base function
    lower_bound = lower_bound.replace(second=0, microsecond=0)
    pages = []
    for page in search_by_title('', 'page'):
        if upper_bound is not None and page.data.last_edited_time > upper_bound:
            continue
        if page.data.last_edited_time < lower_bound:
            break
        pages.append(page)
    logger.debug(pformat(pages, width=print_width))
    return pages


P = ParamSpec('P')


# TODO: integrate into Action
def log_actions(func: Callable[P, bool]) -> Callable[P, bool]:
    # def get_latest_log_path() -> Optional[Path]:
    #     log_path_list = sorted(log_dir.iterdir())
    #     if not log_path_list:
    #         return None
    #     return log_path_list[-1]

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        logger.add(log_dir / '{time}.log',
                   # (get_latest_log_path() or (log_dir / '{time}.log')),
                   level='DEBUG', rotation='100 MB', retention=timedelta(weeks=2))
        logger.info(f'{"#" * 5} Start.')
        with logger.catch():
            has_new_record = func(*args, **kwargs)
            logger.info(f'{"#" * 5} {"Done." if has_new_record else "No new record."}')
            return has_new_record

    wrapper.__signature__ = inspect.signature(func)
    return wrapper


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

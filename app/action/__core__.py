from __future__ import annotations

import inspect
import json
import traceback
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from pprint import pformat
from typing import Iterable, Any, final, Callable, TypeVar, Optional, ParamSpec, cast

import tenacity
from typing_extensions import Self
from uuid import UUID

from loguru import logger

from app import log_dir
from app.my_block import is_template
from notion_df.contents import ParagraphBlockContents, ToggleBlockContents, CodeBlockContents, DividerBlockContents
from notion_df.core.serialization import deserialize_datetime
from notion_df.core.struct import repr_object
from notion_df.core.variable import print_width, my_tz
from notion_df.entity import Page, Workspace, Block
from notion_df.rich_text import RichText, TextSpan, UserMention
from notion_df.user import User, Person


class ActionSkipException(Exception):
    pass


P = ParamSpec("P")
T = TypeVar("T")


def entrypoint(func: Callable[P, T]) -> Callable[P, Optional[T]]:
    """functions with this decorator can handle ActionSkipException,
    therefore, it can be used as the program entrypoint."""

    def get_latest_log_path() -> Optional[Path]:
        log_path_list = sorted(log_dir.iterdir())
        if not log_path_list:
            return None
        return log_path_list[-1]

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        logger.add(
            (get_latest_log_path() or (log_dir / "{time}.log")),
            # log_dir / '{time}.log',
            level="DEBUG",
            rotation="100 MB",
            retention=timedelta(weeks=2),
        )
        logger.info(f'{"#" * 5} Start.')
        with logger.catch(reraise=True):
            try:
                ret = func(*args, **kwargs)
                logger.info(f'{"#" * 5} Done.')
                return ret
            except ActionSkipException as e:
                logger.info(f'{"#" * 5} Skipped : {e.args[0]}')
                return None

    wrapper.__signature__ = inspect.signature(func)
    return cast(Callable[P, Optional[T]], wrapper)


class ActionRecord:
    user = Person(UUID("a007d150-bc67-422c-87db-030a71867dd9"))
    page = Page("6d16dc6747394fca95dc169c8c736e2d")
    page_block = page.as_block()
    last_success_time_parent_block = Block("c66d852e27e84d92b6203dfdadfefad8")
    date_format = "%Y-%m-%d %H:%M:%S+09:00"
    date_group_format = "%Y-%m-%d"

    # Note: the record page is implemented as page with log blocks, not database with log pages,
    #  since 1. Notion API does not directly support permanently deleting pages,
    #  2. third party solutions like `https://github.com/pocc/bulk_delete_notion_pages`
    #  demands additional workload.
    def __init__(self, *, update_last_success_time: bool):
        self.update_last_success_time = update_last_success_time
        self.start_time = datetime.now().astimezone(my_tz)
        self.start_time_str = self.start_time.strftime(self.date_format)
        self.start_time_group_str = self.start_time.strftime(self.date_group_format)
        self.enabled = True
        self.processed_pages: Optional[int] = None

        self.last_success_time_blocks = (
            self.last_success_time_parent_block.retrieve_children()
        )
        last_execution_time_block = self.last_success_time_blocks[0]
        self.last_execution_time_str = cast(
            ParagraphBlockContents, last_execution_time_block.data.contents
        ).rich_text.plain_text
        if self.last_execution_time_str == "STOP":
            raise ActionSkipException("last_execution_time_str == 'STOP'")
        if self.last_execution_time_str == "ALL":
            self.last_success_time = None
        else:
            self.last_success_time = deserialize_datetime(self.last_execution_time_str)

    def __enter__(self) -> Self:
        return self

    def format_time(self) -> str:
        execution_time = datetime.now().astimezone(my_tz) - self.start_time
        return f"{self.start_time_str} - {round(execution_time.total_seconds(), 3)} seconds"

    def __exit__(self, exc_type: type, exc_val, exc_tb) -> None:
        if exc_type is ActionSkipException:
            return
        if exc_type is not None:
            logger.info(
                f'{type(self).__name__}.__exit__() : {exc_type=}, {exc_val=}, exc_tb="""{exc_tb}"""'
            )
        child_block_values = []
        if exc_type is None:
            summary_text = f"success - {self.format_time()}"
            summary_block_value = ParagraphBlockContents(
                RichText([TextSpan(summary_text)])
            )
            if self.update_last_success_time:
                self.last_success_time_parent_block.append_children(
                    [ParagraphBlockContents(RichText([TextSpan(self.start_time_str)]))]
                )
                for block in self.last_success_time_blocks:
                    block.delete(ignore_archived=True)
        elif exc_type in [
            KeyboardInterrupt,
            json.JSONDecodeError,
            tenacity.RetryError,
        ] or "Can't edit block that is archived." in str(exc_val):
            summary_text = f"failure - {self.format_time()}: {exc_val}"
            summary_block_value = ParagraphBlockContents(
                RichText([TextSpan(summary_text)])
            )
        else:
            # TODO: needs full print by redirecting print() stream to logger
            summary_text = (
                f"error - {self.format_time()} - {exc_type.__name__} - {exc_val}"
            )
            summary_block_value = ToggleBlockContents(
                RichText([TextSpan(summary_text), UserMention(self.user)])
            )
            traceback_str = traceback.format_exc()
            child_block_values = []
            # TODO: should be splitting incrementally denser (1000->500->250->...)
            for i in range(0, len(traceback_str), 1000):
                child_block_values.append(
                    CodeBlockContents(
                        RichText.from_plain_text(traceback_str[i : i + 1000])
                    )
                )

        log_group_block = None
        for block in reversed(self.page_block.retrieve_children()):
            if isinstance(block.data.contents, DividerBlockContents):
                log_group_block = self.page_block.append_children(
                    [
                        ToggleBlockContents(
                            RichText([TextSpan(self.start_time_group_str)])
                        )
                    ]
                )[0]
                break
            if (
                cast(ToggleBlockContents, block.data.contents).rich_text.plain_text
                == self.start_time_group_str
            ):
                log_group_block = block
                break
            if self.start_time - block.data.created_time > timedelta(days=7):
                block.delete(ignore_archived=True)
        assert isinstance(log_group_block, Block)

        summary_block = log_group_block.append_children([summary_block_value])[0]
        if child_block_values:
            summary_block.append_children(child_block_values)



class Action(metaclass=ABCMeta):
    def __repr__(self) -> str:
        return repr_object(self)

    @abstractmethod
    def process_pages(self, pages: Iterable[Page]) -> Any:
        """process the given pages."""
        pass

    @abstractmethod
    def process_all(self) -> Any:
        """process with full-scan query."""
        pass

    @final
    def process_by_last_edited_time(
        self, lower_bound: datetime, upper_bound: Optional[datetime] = None
    ) -> Any:
        """process with last-edited-time-based search query.
        Note: Notion APIs' last_edited_time info is only with minutes resolution"""
        logger.info(
            f"{self}.process_by_last_edited_time(): lower_bound - {lower_bound}, upper_bound - {upper_bound}"
        )
        lower_bound = lower_bound.replace(second=0, microsecond=0)
        pages = set()
        for page in Workspace().search_by_title("", "page", page_size=30):
            if upper_bound is not None and page.last_edited_time > upper_bound:
                continue
            if page.last_edited_time < lower_bound:
                break
            pages.add(page)
        logger.debug(f"Before filtered - {pformat(pages, width=print_width)}")
        pages.discard(ActionRecord.page)
        pages = {page for page in pages if not is_template(page)}
        if not pages:
            raise ActionSkipException("No new record.")
        logger.debug(f"After filtered - {pformat(pages, width=print_width)}")
        return self.process_pages(pages)

    @entrypoint
    def run_by_last_edited_time(
        self, lower_bound: datetime, upper_bound: Optional[datetime] = None
    ) -> Any:
        return self.process_by_last_edited_time(lower_bound, upper_bound)

    @entrypoint
    def run_all(self, update_last_success_time: bool = False) -> Any:
        with ActionRecord(update_last_success_time=update_last_success_time):
            return self.process_all()

    @entrypoint
    def run_recent(
        self, interval: timedelta, update_last_success_time: bool = False
    ) -> Any:
        with ActionRecord(
            update_last_success_time=update_last_success_time
        ) as wf_rec:
            return self.process_by_last_edited_time(
                wf_rec.start_time - interval, wf_rec.start_time
            )

    @entrypoint
    def run_from_last_success(self, update_last_success_time: bool) -> Any:
        # TODO: if the last result was RetryError, sleep for 10 mins
        with ActionRecord(
            update_last_success_time=update_last_success_time
        ) as wf_rec:
            if wf_rec.last_success_time is None:
                self.process_all()
            return self.process_by_last_edited_time(wf_rec.last_success_time, None)


class CompositeAction(Action):
    def __init__(self, actions: list[Action]) -> None:
        self.actions = actions

    def process_all(self) -> Any:
        logger.info(f"#### {self}")
        for action in self.actions:
            action.process_all()

    def process_pages(self, pages: Iterable[Page]) -> Any:
        logger.info(f"#### {self}")
        for action in self.actions:
            action.process_pages(pages)


class IndividualAction(Action):
    @final
    def process_all(self) -> Any:
        logger.info(f"#### {self}")
        return self.process_pages(
            page for page in self.query() if not is_template(page)
        )

    @abstractmethod
    def query(self) -> Iterable[Page]:
        pass


class SequentialAction(IndividualAction):
    @final
    def process_pages(self, pages: Iterable[Page]) -> Any:
        logger.info(f"#### {self}")
        for page in pages:
            self.process_page(page)

    @abstractmethod
    def process_page(self, page: Page) -> Any:
        pass

from abc import ABCMeta
from types import new_class
from typing import TypeVar, Any

import pytest

from notion_df.request.request_core import SingleRequest, RequestSettings
from notion_df.util.exception import NotionDfTypeError

not_a_class = TypeVar('not_a_class')


def test_request_form():
    with pytest.raises(NotionDfTypeError):
        # noinspection PyUnusedLocal
        class __TestSingleRequestDefault(SingleRequest):
            def get_body(self) -> Any:
                pass

            def get_settings(self) -> RequestSettings:
                pass

    class __TestSingleRequestArg(SingleRequest[int], metaclass=ABCMeta):
        pass

    assert __TestSingleRequestArg.return_type == int
    assert new_class('test', (SingleRequest[int],)).return_type == int  # type: ignore

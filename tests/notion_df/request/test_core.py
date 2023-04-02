from abc import ABCMeta
from types import new_class
from typing import TypeVar

import pytest

from notion_df.endpoint.core import Request
from notion_df.util.misc import NotionDfValueError

not_a_class = TypeVar('not_a_class')


def test_request_form():
    with pytest.raises(NotionDfValueError):
        class __TestRequestDefault(Request, metaclass=ABCMeta):
            pass

    class __TestRequestArg(Request[int], metaclass=ABCMeta):
        pass

    assert __TestRequestArg.response_type == int
    assert new_class('test', (Request[int],)).response_type == int  # type: ignore

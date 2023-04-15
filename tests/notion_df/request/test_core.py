from abc import ABCMeta
from types import new_class
from typing import TypeVar, Any

import pytest

from notion_df.request.core import Request, RequestSettings
from notion_df.util.misc import NotionDfValueError

not_a_class = TypeVar('not_a_class')


def test_request_form():
    with pytest.raises(NotionDfValueError):
        class __TestRequestDefault(Request):
            def get_body(self) -> Any:
                pass

            def get_settings(self) -> RequestSettings:
                pass

    class __TestRequestArg(Request[int], metaclass=ABCMeta):
        pass

    assert __TestRequestArg.return_type == int
    assert new_class('test', (Request[int],)).return_type == int  # type: ignore

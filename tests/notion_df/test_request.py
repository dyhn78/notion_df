from abc import ABCMeta
from types import new_class

from notion_df.request.core import Response, Request


def test_request_form():
    class __TestRequestDefault(Request, metaclass=ABCMeta):
        pass

    assert __TestRequestDefault.response_type == Response
    assert new_class('test', (Request,)).response_type == Response  # type: ignore

    class __TestRequestArg(Request[int], metaclass=ABCMeta):
        pass

    assert __TestRequestArg.response_type == int
    assert new_class('test', (Request[int],)).response_type == int  # type: ignore

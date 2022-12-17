from abc import ABCMeta
from types import new_class

from notion_df.request.core import Request
from notion_df.resource.core import PlainSerializable


def test_request_form():
    class __TestRequestDefault(Request, metaclass=ABCMeta):
        pass

    assert __TestRequestDefault.response_type == PlainSerializable
    assert new_class('test', (Request,)).response_type == PlainSerializable  # type: ignore

    class __TestRequestArg(Request[int], metaclass=ABCMeta):
        pass

    assert __TestRequestArg.response_type == int
    assert new_class('test', (Request[int],)).response_type == int  # type: ignore

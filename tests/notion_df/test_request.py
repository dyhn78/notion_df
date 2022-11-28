from abc import ABCMeta
from types import new_class

from notion_df.request import Request, Response


def test_request_form():
    class __RequestTestDefault(Request, metaclass=ABCMeta):
        pass

    assert __RequestTestDefault.response_type == Response
    assert new_class('test', (Request,)).response_type == Response  # type: ignore

    class __RequestTestArg(Request[int], metaclass=ABCMeta):
        pass

    assert __RequestTestArg.response_type == int
    assert new_class('test', (Request[int],)).response_type == int  # type: ignore

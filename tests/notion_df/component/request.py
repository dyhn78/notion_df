from abc import ABCMeta
from types import new_class

from notion_df.component.request import RequestForm, ResponseForm


def test_request_form():
    class _RequestFormTestDefault(RequestForm, metaclass=ABCMeta):
        pass

    assert _RequestFormTestDefault.response_type == ResponseForm
    assert new_class('test', (RequestForm,)).response_type == ResponseForm  # type: ignore

    class _RequestFormTestArg(RequestForm[int], metaclass=ABCMeta):
        pass

    assert _RequestFormTestArg.response_type == int
    assert new_class('test', (RequestForm[int],)).response_type == int  # type: ignore

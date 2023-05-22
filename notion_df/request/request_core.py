from __future__ import annotations

import inspect
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from typing import TypeVar, Generic, ClassVar, Any, final, Optional, Iterator, overload

import requests
from requests import JSONDecodeError

from notion_df.util.collection import StrEnum, DictFilter
from notion_df.util.misc import check_classvars_are_defined
from notion_df.util.serialization import DualSerializable, deserialize, serialize, Deserializable
from notion_df.variable import Settings, print_width

MAX_PAGE_SIZE = 100


@dataclass
class Response(Deserializable, metaclass=ABCMeta):
    timestamp: float = field(init=False, default_factory=datetime.now().timestamp)


Response_T = TypeVar('Response_T', bound=Response)
ResponseElement_T = TypeVar('ResponseElement_T', bound=DualSerializable)


@dataclass
class BaseRequest(Generic[Response_T], metaclass=ABCMeta):
    """base request form made of various Resources.
    all non-abstract subclasses must provide class type argument `Response_T`.
    get token from https://www.notion.so/my-integrations"""
    token: str
    return_type: ClassVar[type[Response]]

    def __init_subclass__(cls, **kwargs):
        if inspect.isclass(getattr(cls, 'return_type', None)):
            return
        check_classvars_are_defined(cls)

    @abstractmethod
    def get_settings(self) -> RequestSettings:
        pass

    @abstractmethod
    def get_body(self) -> Any:
        """will be automatically serialized."""
        pass

    @abstractmethod
    def execute(self) -> Response_T:
        """the unified execution method."""
        pass

    @final
    @property
    def headers(self) -> dict[str, Any]:
        return {
            'Authorization': f"Bearer {self.token}",
            'Notion-Version': self.get_settings().version.value,
        }


@dataclass
class RequestSettings:
    version: Version
    method: Method
    url: str


@dataclass
class SingleRequest(BaseRequest[Response_T], metaclass=ABCMeta):
    @final
    def execute(self) -> Response_T:
        settings = self.get_settings()
        response = request(method=settings.method.value, url=settings.url, headers=self.headers, params=None,
                           json=serialize(self.get_body()))
        return self.parse_response_data(response.json())  # nomypy

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> Response_T:
        return cls.return_type.deserialize(data)


class PaginatedRequest(BaseRequest[list[ResponseElement_T]], metaclass=ABCMeta):
    """return_type must be ResponseElement_T (not Response_T)"""
    page_size: int = None

    @overload
    def execute_once(self, *, page_size: int = MAX_PAGE_SIZE) -> dict[str, Any]:
        ...

    @overload
    def execute_once(self, *, start_cursor: Optional[str] = None) -> dict[str, Any]:
        ...

    @final
    def execute_once(self, *, page_size: int = MAX_PAGE_SIZE, start_cursor: Optional[str] = None) -> dict[str, Any]:
        settings = self.get_settings()
        if page_size != MAX_PAGE_SIZE:
            params = {'page_size': page_size}
        elif start_cursor:
            params = {'start_cursor': start_cursor}
        else:
            params = None
        response = request(method=settings.method.value, url=settings.url, headers=self.headers, params=params,
                           json=serialize(self.get_body()))
        return response.json()

    def execute_iter(self) -> Iterator[ResponseElement_T]:
        # TODO: allow entity to use execute_iter() instead of execute()
        page_size_total = self.page_size if self.page_size is not None else float('inf')
        page_size_retrieved = 0

        start_cursor = None
        while page_size_retrieved < page_size_total:
            page_size = min(MAX_PAGE_SIZE, page_size_total - page_size_retrieved)
            page_size_retrieved += page_size
            if start_cursor:
                data = self.execute_once(start_cursor=start_cursor)
            else:
                data = self.execute_once(page_size=page_size)
            yield from self.parse_response_data(data)
            if not data['has_more']:
                return
            start_cursor = data['next_cursor']
        return

    def execute(self) -> list[ResponseElement_T]:
        return list(self.execute_iter())

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> list[ResponseElement_T]:
        element_list = []
        for data_element in data['results']:
            element_list.append(deserialize(cls.return_type, data_element))
        return element_list

    @classmethod
    def parse_response_data_list(cls, data_list: list[dict[str, Any]]) -> list[ResponseElement_T]:
        element_list = []
        for data in data_list:
            for data_element in data['results']:
                element_list.append(deserialize(cls.return_type, data_element))
        return element_list


def request(*, method: str, url: str, headers: dict[str, Any], params: Any, json: Any) -> requests.Response:
    if Settings.print:
        pprint(dict(method=method, url=url, headers=headers, params=params, json=json), width=print_width)
    response = requests.request(method, url, headers=headers, params=params, json=json)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            raise requests.exceptions.HTTPError(response.json())
        except JSONDecodeError:
            raise requests.exceptions.HTTPError(response.text)
    return response


class Method(StrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    # HEAD = 'HEAD'
    # OPTIONS = 'OPTIONS'


class Version(StrEnum):
    v20220222 = '2022-02-22'
    v20220628 = '2022-06-28'

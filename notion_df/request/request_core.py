from __future__ import annotations

import inspect
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from typing import TypeVar, Generic, Any, final, Optional, Iterator

import requests
from requests import JSONDecodeError

from notion_df.util.collection import StrEnum
from notion_df.util.exception import NotionDfValueError
from notion_df.util.misc import check_classvars_are_defined
from notion_df.util.serialization import DualSerializable, deserialize, serialize, Deserializable
from notion_df.variable import Settings, print_width

MAX_PAGE_SIZE = 100


@dataclass
class Response(Deserializable, metaclass=ABCMeta):
    timestamp: float = field(init=False, default_factory=datetime.now().timestamp)


Response_T = TypeVar('Response_T', bound=Response)
ResponseElement_T = TypeVar('ResponseElement_T', bound=Response | DualSerializable)


@dataclass
class BaseRequest(metaclass=ABCMeta):
    """base request form made of various Resources.
    all non-abstract subclasses must provide class type argument `Response_T`.
    get token from https://www.notion.so/my-integrations"""
    token: str

    @abstractmethod
    def get_settings(self) -> RequestSettings:
        pass

    @abstractmethod
    def get_body(self) -> Any:
        """will be automatically serialized."""
        pass

    @abstractmethod
    def execute(self) -> Response:
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


class SingleRequest(Generic[Response_T], BaseRequest, metaclass=ABCMeta):
    response_type: type[Response_T]  # TODO define assert

    @final
    def execute(self) -> Response_T:
        settings = self.get_settings()
        response = request(method=settings.method.value, url=settings.url, headers=self.headers, params=None,
                           json=serialize(self.get_body()))
        return self.parse_response_data(response.json())  # nomypy

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> Response_T:
        return cls.response_type.deserialize(data)


class PaginatedRequest(Generic[ResponseElement_T], BaseRequest, metaclass=ABCMeta):
    response_element_type: type[ResponseElement_T]  # TODO define assert
    page_size: int = None
    # TODO: remove page_size
    #  - execute() returns PaginatedResponse instead of builtin iterator (which supports getitem by slice)

    @final
    def execute_once(self, page_size: int = MAX_PAGE_SIZE, start_cursor: Optional[str] = None) -> dict[str, Any]:
        settings = self.get_settings()
        body = self.get_body()

        pagination_params = {}
        if page_size != MAX_PAGE_SIZE:
            pagination_params.update({'page_size': page_size})
        if start_cursor:
            pagination_params.update({'start_cursor': start_cursor})

        if settings.method.value == Method.GET:
            params = pagination_params
        elif settings.method.value == Method.POST:
            params = None
            if body is None:
                body = {}
            body.update(pagination_params)
        else:
            raise NotionDfValueError('bad method', {'method': settings.method})

        response = request(method=settings.method.value, url=settings.url, headers=self.headers, params=params,
                           json=serialize(body))
        return response.json()

    def execute(self) -> Iterator[ResponseElement_T]:
        page_size_total = self.page_size if self.page_size is not None else float('inf')
        page_size_retrieved = 0

        start_cursor = None
        while page_size_retrieved < page_size_total:
            page_size = min(MAX_PAGE_SIZE, page_size_total - page_size_retrieved)
            page_size_retrieved += page_size
            data = self.execute_once(page_size, start_cursor)
            yield from self.parse_response_data(data)
            if not data['has_more']:
                return
            start_cursor = data['next_cursor']
        return

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> Iterator[ResponseElement_T]:
        for data_element in data['results']:
            yield deserialize(cls.response_element_type, data_element)


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

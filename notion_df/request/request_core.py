from __future__ import annotations

import inspect
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from typing import TypeVar, Generic, ClassVar, Any, final, Optional

import requests
from requests import JSONDecodeError

import notion_df.variable
from notion_df.util.collection import StrEnum, DictFilter
from notion_df.util.misc import check_classvars_are_defined
from notion_df.util.serialization import DualSerializable, deserialize, serialize, Deserializable

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
        response = request(method=settings.method.value, url=settings.url, headers=self.headers,
                           json=serialize(self.get_body()))
        return self.parse_response_data(response.json())  # nomypy

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> Response_T:
        return cls.return_type.deserialize(data)


class PaginatedRequest(BaseRequest[list[ResponseElement_T]], metaclass=ABCMeta):
    """return_type must be ResponseElement_T (not Response_T)"""
    page_size: int

    @final
    def request_once(self, page_size: int = MAX_PAGE_SIZE, start_cursor: Optional[str] = None) -> dict[str, Any]:
        if page_size == MAX_PAGE_SIZE and start_cursor is None:
            body = self.get_body()
        else:
            body = DictFilter.not_none({
                'page_size': page_size,
                'start_cursor': start_cursor,
                **self.get_body()
            })
        settings = self.get_settings()
        response = request(method=settings.method.value, url=settings.url, headers=self.headers, json=serialize(body))
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                raise requests.exceptions.HTTPError(response.json())
            except JSONDecodeError:
                raise requests.exceptions.HTTPError(response.text)
        return response.json()

    def execute(self) -> list[ResponseElement_T]:
        page_size_total = self.page_size
        if page_size_total == -1:
            page_size_total = float('inf')
        page_size_retrieved = 0

        start_cursor = None
        data_list = []
        while page_size_retrieved < page_size_total:
            page_size = min(MAX_PAGE_SIZE, page_size_total - page_size_retrieved)
            page_size_retrieved += page_size

            data = self.request_once(page_size, start_cursor)
            data_list.append(data)
            if not data['has_more']:
                break
            start_cursor = data['next_cursor']

        return self.parse_response_data_list(data_list)

    @classmethod
    def parse_response_data_list(cls, data_list: list[dict[str, Any]]) -> list[ResponseElement_T]:
        element_list = []
        for data in data_list:
            for data_element in data['results']:
                element_list.append(deserialize(cls.return_type, data_element))
        return element_list


def request(*, method: str, url: str, headers: dict[str, Any], json: Any):
    if notion_df.variable.settings_print_body:
        pprint(dict(method=method, url=url, headers=headers, json=json), width=160)
    response = requests.request(method, url, headers=headers, json=json)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise requests.exceptions.HTTPError(response.json())
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

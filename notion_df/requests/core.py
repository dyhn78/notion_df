from __future__ import annotations

import inspect
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from functools import cache
from typing import TypeVar, Generic, ClassVar, get_args, Any, final, Optional

from requests import Response, request

from notion_df.objects.core import DualSerializable, serialize, deserialize
from notion_df.utils.collection import StrEnum
from notion_df.utils.misc import NotionDfValueError

Response_T = TypeVar('Response_T', bound=DualSerializable)
ResponseElement_T = TypeVar('ResponseElement_T', bound=DualSerializable)
MAX_PAGE_SIZE = 100


@dataclass
class BaseRequest(Generic[Response_T], metaclass=ABCMeta):
    """base request form made of various Resources.
    type argument `Response_T` is strongly recommended on subclassing.
    get api_key from https://www.notion.so/my-integrations"""
    api_key: str
    return_type: ClassVar[type[DualSerializable]]

    def __init_subclass__(cls, **kwargs):
        try:
            generic_class = cls.__orig_bases__[0]  # type: ignore
            return_type = get_args(generic_class)[0]
            if not inspect.isabstract(cls) and isinstance(return_type, TypeVar):
                raise ValueError
        except (AttributeError, IndexError, ValueError):
            raise NotionDfValueError('Request must have explicit response data type (not TypeVar)', {'cls': cls})
        cls.return_type = return_type

    @abstractmethod
    @cache
    def get_settings(self) -> RequestSettings:
        pass

    @abstractmethod
    def get_body(self) -> Any:
        pass

    @abstractmethod
    def request(self) -> Response_T:
        pass


@dataclass
class Request(BaseRequest[Response_T], metaclass=ABCMeta):
    @final
    def request(self) -> Response_T:
        response = self.get_settings().request(self.api_key, self.get_body())
        response.raise_for_status()
        return self.parse_response_data(response.json())  # nomypy

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> Response_T:
        return cls.return_type.deserialize(data)


class PaginatedRequest(BaseRequest[list[ResponseElement_T]], metaclass=ABCMeta):
    page_size: int

    @final
    def request_once(self, page_size: int = MAX_PAGE_SIZE, start_cursor: Optional[str] = None) -> dict[str, Any]:
        if page_size == MAX_PAGE_SIZE and start_cursor is None:
            body = self.get_body()
        else:
            body = {
                       'page_size': page_size,
                       'start_cursor': start_cursor
                   } | self.get_body()
        response = self.get_settings().request(self.api_key, body)
        response.raise_for_status()
        return response.json()

    def request(self) -> list[ResponseElement_T]:
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


@dataclass
class RequestSettings:
    """
    - version: Version (enum)
    - method: Method
    - url: str
    """
    version: Version
    method: Method
    url: str

    def request(self, api_key: str, body: Any) -> Response:
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Notion-Version': self.version.value,
        }
        return request(self.method.value, self.url, headers=headers, data=serialize(body))


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

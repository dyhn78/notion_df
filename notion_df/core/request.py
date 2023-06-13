from __future__ import annotations

import inspect
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from typing import TypeVar, Generic, Any, final, Optional, Iterator, Sequence, overload

import requests
from requests import JSONDecodeError
from tenacity import retry, wait_exponential, stop_after_attempt
from typing_extensions import Self

from notion_df.core.exception import NotionDfValueError, NotionDfIndexError, NotionDfTypeError
from notion_df.core.serialization import deserialize, serialize, Deserializable
from notion_df.util.collection import StrEnum
from notion_df.util.misc import repr_object
from notion_df.variable import Settings, print_width

MAX_PAGE_SIZE = 100


@retry(wait=wait_exponential(multiplier=1, min=4, max=180, stop=stop_after_attempt(10)))
def request(*, method: str, url: str, headers: dict[str, Any], params: Any, json: Any) -> requests.Response:
    if Settings.print:
        pprint(dict(method=method, url=url, headers=headers, params=params, json=json), width=print_width)
    with requests.request(method, url, headers=headers, params=params, json=json, timeout=30) as response:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                raise requests.exceptions.HTTPError(response.json())
            except JSONDecodeError:
                raise requests.exceptions.HTTPError(response.text)
        return response


@dataclass
class Response(Deserializable, metaclass=ABCMeta):
    timestamp: float = field(init=False, default_factory=datetime.now().timestamp)
    raw_data: dict[str, Any] = field(init=False, default=None)

    @classmethod
    def _deserialize_this(cls, raw_data: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw_data, raw_data=raw_data)


Response_T = TypeVar('Response_T', bound=Response)
ResponseElement_T = TypeVar('ResponseElement_T')


@dataclass
class BaseRequest(metaclass=ABCMeta):
    # TODO: refactor so that Request has entity information
    #  - Request.execute() returns Paginator
    #  - Paginator can interact with Request instance and able to call Entity._send_response()
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
    response_type: type[Response_T]

    def __init_subclass__(cls, **kwargs):
        if not inspect.isabstract(cls):
            assert cls.response_type

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
    response_element_type: type[ResponseElement_T]
    page_size: int = None  # TODO - AS-IS: total size of all pages summed, TO-BE: each request size

    def __init_subclass__(cls, **kwargs):
        if not inspect.isabstract(cls):
            assert cls.response_element_type

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


T = TypeVar('T')


class Paginator(Sequence[T]):
    def __init__(self, element_type: type[T], it: Iterator[T]):
        self.element_type: type[T] = element_type
        """used on repr()"""
        self._it: Iterator[T] = it
        self._values: list[T] = []

    def __repr__(self):
        return repr_object(self, element_type=self.element_type)

    def _fetch_until(self, index: int) -> None:
        """fetch until self._values[index] is possible"""
        while len(self._values) <= index:
            try:
                self._values.append(next(self._it))
            except StopIteration:
                raise NotionDfIndexError("Index out of range", {'self': self, 'index': index})

    def _fetch_all(self) -> None:
        for element in self._it:
            self._values.append(element)

    def __len__(self):
        self._fetch_all()
        return len(self._values)

    @overload
    def __getitem__(self, index_or_id: int) -> T:
        ...

    @overload
    def __getitem__(self, index_or_id: slice) -> list[T]:
        ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        if isinstance(index, int):
            if index >= 0:
                self._fetch_until(index)
            else:
                self._fetch_all()
            return self._values[index]
        if isinstance(index, slice):
            step = index.step if index.step is not None else 1

            if ((index.start is not None and index.start < 0)
                    or (index.stop is not None and index.stop < 0)
                    or (index.stop is None and step > 0)
                    or (index.start is None and step < 0)):
                self._fetch_all()
                return self._values[index]

            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else 0
            try:
                self._fetch_until(max(start, stop))
            except NotionDfIndexError:
                pass
            return [self._values[start:stop:step]]
        else:
            raise NotionDfTypeError("bad argument - expected int or slice", {'self': self, 'index': index})

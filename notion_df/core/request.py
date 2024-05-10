from __future__ import annotations

import inspect
import pprint
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import TypeVar, Generic, Any, final, Optional, Iterator, Sequence, overload

import requests.exceptions
import tenacity
from loguru import logger
from requests import Response

from notion_df.core.data import EntityDataT
from notion_df.core.exception import NotionDfValueError, NotionDfIndexError, NotionDfTypeError
from notion_df.core.serialization import deserialize, serialize
from notion_df.util.collection import PlainStrEnum
from notion_df.util.misc import repr_object
from notion_df.variable import print_width

MAX_PAGE_SIZE = 100


@dataclass
class Request:
    # TODO: async with throttling  https://chat.openai.com/c/adcf80cd-d800-4fef-bfa9-56c548e0058a
    method: Method
    url: str
    headers: dict[str, Any]
    params: Any
    json: Any

    @staticmethod
    def is_server_error(exception: BaseException) -> bool:
        if isinstance(exception, RequestError):
            status_code = exception.response.status_code
            return 500 <= status_code < 600 or status_code == 409  # conflict
        return any(isinstance(exception, cls) for cls in [requests.exceptions.ReadTimeout,
                                                          requests.exceptions.ChunkedEncodingError,
                                                          # requests.exceptions.SSLError,
                                                          ])

    @tenacity.retry(wait=tenacity.wait_none(),
                    stop=tenacity.stop_after_attempt(3),
                    retry=tenacity.retry_if_exception(is_server_error))  # TODO: add request info on TimeoutError
    def execute(self) -> Response:
        logger.debug(self)
        response = requests.request(method=self.method.value, url=self.url, headers=self.headers,
                                    params=self.params, json=self.json, timeout=80)  # TODO: relate with tenacity
        logger.trace(pprint.pformat(response.text, width=print_width))
        try:
            response.raise_for_status()
            return response
        except requests.HTTPError:
            e = RequestError(self, response)
            logger.debug(e)
            raise e


class RequestError(Exception):
    request: Request
    response: Response
    raw_data: Any
    """ex) {'object': 'error', 'status': 400, 'code': 'validation_error', 
    'message': 'Unsaved transactions: Invalid value for property with limit'}"""
    code: str = ''
    """ex) 'validation_error'"""
    message: str = ''
    """ex) 'Unsaved transactions: Invalid value for property with limit'"""

    def __init__(self, request: Request, response: Response):
        self.response = response
        self.request = request
        try:
            self.raw_data = self.response.json()
            self.code = self.raw_data['code']
            self.message = self.raw_data['message']
        except requests.JSONDecodeError:
            self.raw_data = self.response.text
        except KeyError as e:  # unexpected error format
            raise KeyError(*e.args, self.raw_data)

    def __str__(self) -> str:
        return repr_object(self, self.raw_data, request=self.request)


@dataclass
class RequestBuilder(metaclass=ABCMeta):
    # TODO: make it more functional-programming-like
    #  page_create_request: Request = Request.build()
    #  database_query_request: PaginatedRequest = PaginatedRequest.build()
    """base request form made of various Resources.
    all non-abstract subclasses must provide class type argument `EntityDataT`.
    get token from https://www.notion.so/my-integrations"""
    token: str

    @abstractmethod
    def get_settings(self) -> RequestSettings:
        pass

    @abstractmethod
    def get_body(self) -> Any:
        """will not be automatically serialized."""
        pass

    @abstractmethod
    def execute(self):
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


class Method(PlainStrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    # HEAD = 'HEAD'
    # OPTIONS = 'OPTIONS'


class Version(PlainStrEnum):
    v20220222 = '2022-02-22'
    v20220628 = '2022-06-28'


class SingleRequestBuilder(Generic[EntityDataT], RequestBuilder, metaclass=ABCMeta):
    data_type: type[EntityDataT]

    def __init_subclass__(cls, **kwargs):
        if not inspect.isabstract(cls):
            assert cls.data_type

    @final
    def execute(self) -> EntityDataT:
        settings = self.get_settings()
        response = Request(method=settings.method, url=settings.url, headers=self.headers, params=None,
                           json=self.get_body()).execute()
        return self.parse_response_data(response.json())  # nomypy

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> EntityDataT:
        return cls.data_type.deserialize(data)


DataElementT = TypeVar('DataElementT')


class PaginatedRequestBuilder(Generic[DataElementT], RequestBuilder, metaclass=ABCMeta):
    data_element_type: type[DataElementT]
    page_size: int = None  # TODO - AS-IS: total size of all pages summed, TO-BE: each request size

    def __init_subclass__(cls, **kwargs):
        if not inspect.isabstract(cls):
            assert cls.data_element_type

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

        response = Request(method=settings.method, url=settings.url, headers=self.headers, params=params,
                           json=serialize(body)).execute()
        return response.json()

    def execute(self) -> Iterator[DataElementT]:
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
    def parse_response_data(cls, data: dict[str, Any]) -> Iterator[DataElementT]:
        for data_element in data['results']:
            yield deserialize(cls.data_element_type, data_element)


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

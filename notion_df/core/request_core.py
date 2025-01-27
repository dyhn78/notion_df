from __future__ import annotations

import inspect
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Generic, Any, final, Optional, Iterator

import requests.exceptions
import tenacity
from loguru import logger
from requests import Response

from notion_df.core.collection import PlainStrEnum
from notion_df.core.data_core import EntityDataT
from notion_df.core.exception import ImplementationError, NotionDfException
from notion_df.core.serialization import serialize
from notion_df.core.struct import repr_object

MAX_PAGE_SIZE = 100


def is_server_error(exception: BaseException) -> bool:
    if isinstance(exception, RequestError):
        status_code = exception.response.status_code
        return 500 <= status_code < 600 or status_code == 409  # conflict
    if isinstance(exception, requests.exceptions.RequestException):
        return any(isinstance(exception, cls) for cls in [
            requests.exceptions.ReadTimeout,
            requests.exceptions.ChunkedEncodingError,
            # requests.exceptions.SSLError,
        ])
    if isinstance(exception, requests.exceptions.ConnectionError):
        return 'Connection aborted.' == exception.args[0]
    return False


@dataclass(frozen=True)
class Request:
    """request builder tailored to Notion API."""
    # TODO: rename to RequestBuilder
    # TODO: async with throttling  https://chat.openai.com/c/adcf80cd-d800-4fef-bfa9-56c548e0058a
    token: str
    method: Method
    version: Version
    path: str
    params: Any
    json: Any

    @property
    def headers(self) -> dict[str, Any]:
        return {
            'Authorization': f"Bearer {self.token}",
            'Notion-Version': self.version.value,
        }

    @property
    def url(self) -> str:
        return f"{self.version.base_url.rstrip('/')}/{self.path.lstrip('/')}"

    @tenacity.retry(wait=tenacity.wait_none(),
                    stop=tenacity.stop_after_attempt(3),
                    retry=tenacity.retry_if_exception(is_server_error))  # TODO: add request info on TimeoutError
    def execute(self) -> Response:
        logger.debug(self)
        response = requests.request(method=self.method.value, url=self.url, headers=self.headers,
                                    params=self.params, json=self.json, timeout=80)  # TODO: relate with tenacity
        try:
            response.raise_for_status()
            return response
        except requests.HTTPError:
            e = RequestError(self, response)
            logger.debug(e)
            raise e


class RequestError(NotionDfException):
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
            raise RuntimeError("Unexpected error format.", *e.args, self.raw_data)

    def __str__(self) -> str:
        return repr_object(self, self.raw_data, request=self.request)


class Method(PlainStrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class Version(PlainStrEnum):
    v20220222 = '2022-02-22'
    v20220628 = '2022-06-28'

    def __str__(self):
        return repr_object(self, self.value)

    @property
    def base_url(self) -> str:
        return 'https://api.notion.com/v1'


@dataclass
class RequestSettings:
    version: Version
    method: Method
    path: str


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


class SingleRequestBuilder(Generic[EntityDataT], RequestBuilder, metaclass=ABCMeta):
    data_type: type[EntityDataT]

    def __init_subclass__(cls, **kwargs):
        if not inspect.isabstract(cls):
            assert cls.data_type

    @final
    def execute(self) -> EntityDataT:
        settings = self.get_settings()
        response = Request(token=self.token, method=settings.method, path=settings.path, version=settings.version,
                           params=None, json=self.get_body()).execute()
        return self.parse_response_data(response.json())  # nomypy

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> EntityDataT:
        return cls.data_type.deserialize(data).set_latest()


class PaginatedRequestBuilder(Generic[EntityDataT], RequestBuilder, metaclass=ABCMeta):
    data_element_type: type[EntityDataT]
    page_size: int  # TODO - AS-IS: total size of all pages summed, TO-BE: each request size

    def __init_subclass__(cls, **kwargs):
        if not inspect.isabstract(cls):
            assert cls.data_element_type

    @final
    def execute(self) -> Iterator[EntityDataT]:
        start_cursor = None
        while True:
            data = request_page(self, self.page_size, start_cursor)
            yield from self.parse_response_data(data)
            if not data['has_more']:
                return
            start_cursor = data['next_cursor']

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> Iterator[EntityDataT]:
        for data_element in data['results']:
            yield cls.data_element_type.deserialize(data_element).set_latest()


def request_page(self: RequestBuilder, page_size: Optional[int] = MAX_PAGE_SIZE,
                 start_cursor: Optional[str] = None) -> dict[str, Any]:
    settings = self.get_settings()
    body = self.get_body()

    pagination_params = {}
    if page_size not in {MAX_PAGE_SIZE, None}:
        pagination_params.update({'page_size': page_size})
    if start_cursor:
        pagination_params.update({'start_cursor': start_cursor})

    match settings.method:
        case Method.GET:
            params = pagination_params
        case Method.POST:
            params = None
            if body is None:
                body = {}
            body.update(pagination_params)
        case _:
            raise ImplementationError(f'Invalid method. {type(self)=}')

    response = Request(token=self.token, method=settings.method, path=settings.path, version=settings.version,
                       params=params, json=serialize(body)).execute()
    return response.json()

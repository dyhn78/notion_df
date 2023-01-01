from __future__ import annotations

import inspect
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import TypeVar, Generic, ClassVar, get_args, Any, final

import requests
from html5lib import serialize

from notion_df.resource.core import Deserializable
from notion_df.util.collection import StrEnum
from notion_df.util.misc import NotionDfValueError

Response_T = TypeVar('Response_T', bound=Deserializable)


@dataclass
class Request(Generic[Response_T], metaclass=ABCMeta):
    """base request form made of various Resources.
    type argument `Response_T` is strongly recommended on subclassing.
    get api_key from https://www.notion.so/my-integrations"""
    response_type: ClassVar[type[Deserializable]]
    api_key: str

    def __init_subclass__(cls, **kwargs):
        try:
            generic_class = cls.__orig_bases__[0]  # type: ignore
            response_type = get_args(generic_class)[0]
            if not inspect.isclass(response_type):
                raise ValueError
        except (AttributeError, ValueError):
            raise NotionDfValueError('Request must have explicit response data type', {'cls': cls})
        cls.response_type = response_type

    @abstractmethod
    def get_settings(self) -> RequestSettings:
        pass

    @abstractmethod
    def get_body(self) -> Any:
        pass

    @final
    def request(self) -> Response_T:
        settings = self.get_settings()
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Notion-Version': settings.version.value,
        }
        response = requests.request(settings.method.value, settings.url,
                                    headers=headers, data=serialize(self.get_body()))
        response.raise_for_status()
        return self.response_type.deserialize(response.json())


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


class Method(StrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    # HEAD = 'HEAD'
    # OPTIONS = 'OPTIONS'


class Version(StrEnum):
    v20220628 = '2022-06-28'

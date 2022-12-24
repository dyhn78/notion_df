from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import TypeVar, Generic, ClassVar, get_args, Any, final, Literal

import requests

from notion_df.resource.core import Serializable, PlainSerializable  # PlainSerializable
from notion_df.util.mixin import input_based_cache

Response_T = TypeVar('Response_T', bound=Serializable)


@dataclass
class Request(Generic[Response_T], metaclass=ABCMeta):
    """base request form made of various Resources.
    type argument `Response_T` is strongly recommended on subclassing.
    get api_key from https://www.notion.so/my-integrations"""
    response_type: ClassVar[type[Response_T]]
    api_key: str

    def __init_subclass__(cls, **kwargs):
        try:
            generic_class = cls.__orig_bases__[0]  # type: ignore
            response_type = get_args(generic_class)[0]
            if response_type == Response_T:
                raise ValueError
        except (AttributeError, ValueError):
            # TODO - change to ValueError?
            print(f'WARNING: {cls.__name__} does not have explicit response data type, use PlainSerializable instead')
            response_type = PlainSerializable
        cls.response_type = response_type

    @classmethod
    @abstractmethod
    @input_based_cache
    def get_settings(cls) -> RequestSettings:
        pass

    @abstractmethod
    def get_path(self) -> str:
        pass

    @abstractmethod
    def get_body(self) -> Any:
        pass

    @final
    def request(self) -> Response_T:
        settings = self.get_settings()
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Notion-Version': settings.notion_version,
        }
        response = requests.request(settings.method, f'{settings.endpoint}{self.get_path()}',
                                    data=self.get_body(), headers=headers)
        response.raise_for_status()
        return self.response_type.deserialize(response.json())


@dataclass
class RequestSettings:
    notion_version: str
    endpoint: str
    method: Literal['GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']

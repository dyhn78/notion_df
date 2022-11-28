from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Literal, TypeVar, Any, Generic, final, ClassVar, get_args

import requests
from typing_extensions import Self

from notion_df.util.mixin import input_based_cache

ResponseForm_T = TypeVar('ResponseForm_T', bound='ResponseForm')


@dataclass
class ResponseForm:
    @classmethod
    @abstractmethod
    def parse(cls, response: dict | list) -> Self:
        pass


@dataclass
class RequestSettings(Generic[ResponseForm_T]):
    notion_version: str
    endpoint: str
    method: Literal['GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']


@dataclass
class RequestForm(Generic[ResponseForm_T], metaclass=ABCMeta):
    """base request form. type argument `ResponseForm_T` is strongly recommended."""
    response_type: ClassVar[type[ResponseForm_T]]
    api_key: str

    def __init_subclass__(cls, **kwargs):
        try:
            generic_class = cls.__orig_bases__[0]  # type: ignore
            response_type = get_args(generic_class)[0]
        except (AttributeError, IndexError):
            print(f'WARNING: {cls.__name__} does not have response type')
            response_type = ResponseForm
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
    def request(self) -> ResponseForm_T:
        settings = self.get_settings()
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Notion-Version': settings.notion_version,
        }
        response = requests.request(settings.method, f'{settings.endpoint}{self.get_path()}',
                                    data=self.get_body(), headers=headers)
        response.raise_for_status()
        return self.response_type.parse(response.json())

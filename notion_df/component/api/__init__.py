from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Literal, TypeVar, Any, Generic, final

import requests
from typing_extensions import Self

NotionResponse_T = TypeVar('NotionResponse_T', bound='NotionResponse')


@dataclass
class NotionResponse(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def parse(cls, response: dict | list) -> Self:
        pass


@dataclass
class NotionRequestSettings(Generic[NotionResponse_T]):
    notion_version: str
    endpoint: str
    method: Literal['GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']
    response_type: type[NotionResponse_T]


@dataclass
class NotionRequest(Generic[NotionResponse_T], metaclass=ABCMeta):
    api_key: str

    @classmethod
    @abstractmethod
    def get_settings(cls) -> NotionRequestSettings:
        pass

    @abstractmethod
    def get_path(self) -> str:
        pass

    @abstractmethod
    def get_body(self) -> Any:
        pass

    @final
    def request(self) -> NotionResponse_T:
        settings = self.get_settings()
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Notion-Version': settings.notion_version,
        }
        response = requests.request(settings.method, f'{settings.endpoint}{self.get_path()}',
                                    data=self.get_body(), headers=headers)
        response.raise_for_status()
        return settings.response_type.parse(response.json())

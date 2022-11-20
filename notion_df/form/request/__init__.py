from __future__ import annotations

from abc import abstractmethod, ABCMeta


class RequestBuilder(metaclass=ABCMeta):
    ENDPOINT = "https://api.notion.com/v1/"

    @classmethod
    @abstractmethod
    def _get_entrypoint(cls):
        pass

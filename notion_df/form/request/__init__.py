from __future__ import annotations

from abc import abstractmethod, ABCMeta

from notion_df.util.mixin import input_based_cache

NOTION_VERSION = '2022-06-28'


@input_based_cache
def _get_headers(notion_api_key: str):
    return {
        'Authorization': f"Bearer {notion_api_key}",
        'Notion-Version': NOTION_VERSION,
    }


class RequestBuilder(metaclass=ABCMeta):
    ENDPOINT = "https://api.notion.com/v1/"

    def __init__(self, notion_api_key: str):
        self.headers = _get_headers(notion_api_key)

    @classmethod
    @abstractmethod
    def _get_entrypoint(cls):
        pass

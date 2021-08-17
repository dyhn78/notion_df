from collections import defaultdict
from pprint import pprint

from .page import PageParser


class PageListParser(list):
    def __init__(self, page_parsers: list[PageParser]):
        super().__init__(page_parsers)

    def __getitem__(self, index) -> PageParser:
        return super().__getitem__(index)

    @classmethod
    def fetch_query(cls, response: dict):
        return cls([PageParser.fetch_query_frag(page_result)
                    for page_result in response['results']])

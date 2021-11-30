from __future__ import annotations

from collections import defaultdict
from pprint import pprint
from typing import Iterator, Callable, Any

from notion_client import APIResponseError

from notion_zap.cli.struct import PropertyFrame
from notion_zap.cli.gateway import requestors
from .database import Database
from .page_row import PageRow
from ..base import BlockEditor
from ..common.with_children import BlockChildren


class PageList(BlockChildren):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame

        from .pagelist_agents import PageListUpdater, PageListCreator
        self.update = PageListUpdater(self)
        self.create = PageListCreator(self)

        self._by_id = {}
        self._by_title = defaultdict(list)

    def open_page(self, page_id: str):
        return PageRow(caller=self, page_id=page_id, frame=self.frame)

    def create_page(self):
        return PageRow(caller=self, page_id='', frame=self.frame)

    def attach(self, page: PageRow):
        if page.yet_not_created:
            self.create.attach_page(page)
        else:
            self.update.attach_page(page)

    def detach(self, page: PageRow):
        if page.yet_not_created:
            self.create.detach_page(page)
        else:
            self.update.detach_page(page)

    def open_query(self) -> QueryWithCallback:
        def callback(response):
            return self.update.apply_query_response(response)

        return QueryWithCallback(self, self.frame, callback)

    def fetch(self, page_id: str):
        """this will first try to search the page in local base,
        then make a request (RetrievePage).
        returns child_page if succeed, otherwise returns None."""
        if page := self.by_id.get(page_id):
            return page
        page = self.open_page(page_id)
        try:
            page.props.retrieve()
            return page
        except APIResponseError:
            self.detach(page)
            return None

    def save(self):
        self.update.save()
        response = self.create.save()
        self.update.blocks.extend(response)

    def save_info(self):
        return {'pages': self.update.save_info(),
                'new_pages': self.create.save_info()}

    def save_required(self):
        return (self.update.save_required()
                or self.create.save_required())

    @property
    def by_id(self) -> dict[str, PageRow]:
        return self._by_id

    @property
    def by_title(self) -> dict[str, list[PageRow]]:
        return self._by_title

    def list_all(self):
        return self.update.blocks + self.create.blocks

    def iter_all(self) -> Iterator[PageRow]:
        return iter(self.list_all())

    def iter_valids(self, exclude_archived_blocks=True,
                    exclude_yet_not_created_blocks=True) -> list[PageRow]:
        for child in self.iter_all():
            if exclude_archived_blocks and child.archived:
                continue
            if exclude_yet_not_created_blocks and child.yet_not_created:
                continue
            yield child

    def list_valids(self, exclude_archived_blocks=True,
                    exclude_yet_not_created_blocks=True):
        return list(self.iter_valids(
            exclude_archived_blocks, exclude_yet_not_created_blocks))

    def __iter__(self) -> Iterator[PageRow]:
        return self.iter_all()

    def by_value_of(self, prop_key: str):
        res = defaultdict(list)
        for page in self.list_all():
            res[page.props.read_of(prop_key)].append(page)
        return res

    def by_value_at(self, prop_tag: str):
        return self.by_value_of(self.frame.key_at(prop_tag))

    def by_idx_of(self, prop_key: str):
        try:
            res = {}
            for page in self.list_all():
                res[page.props.read_of(prop_key)] = page
            return res
        except TypeError:
            page_object = self.list_all()[0]
            pprint(f"key : {page_object.props.read_of(prop_key)}")
            pprint(f"value : {page_object.block_id}")
            raise TypeError

    def by_idx_at(self, prop_tag: str):
        return self.by_idx_of(self.frame.key_at(prop_tag))


class QueryWithCallback(requestors.Query):
    def __init__(self, editor: BlockEditor, frame: PropertyFrame,
                 execute_callback: Callable[[Any], list[PageRow]]):
        super().__init__(editor, frame)
        self.callback = execute_callback

    def execute(self, request_size=0, print_heads=0):
        # TODO: 수가 적으면 페이지 제목을 모두 (리스트 형태로) 프린트하게 수정
        response = super().execute(request_size)
        pages = self.callback(response)
        if pages and print_heads:
            heads = [(page.title, page.block_url) for page in pages[:print_heads]]
            if pages[print_heads:]:
                heads.append(('...', '...'))
            try:
                pprint(heads)
            except AttributeError:  # this happens when called from pythonw.exe
                pass
        return pages

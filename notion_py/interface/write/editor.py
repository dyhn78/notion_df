from __future__ import annotations
from collections import defaultdict
from pprint import pprint

from notion_py.interface.parse import PageProperty, PagePropertyList, BlockChildren
from notion_py.interface.read import Query, RetrievePage, GetBlockChildren
from notion_py.interface.write import UpdateBasicPage, UpdateTabularPage, AppendBlockChildren, \
    BasicPagePropertyStack
from .constants import DEFAULT_OVERWRITE, DEFAULT_EDIT_MODE


class BasicPageEditor:
    def __init__(self, parsed_page: PageProperty,
                 parent_id='', blocks_edit_mode=DEFAULT_EDIT_MODE):
        self.page_id = parsed_page.page_id
        self.title = parsed_page.title
        if not parent_id:
            self.parent_id = parsed_page.parent_id
        else:
            self.parent_id = parent_id

        self._update_props = UpdateBasicPage(parsed_page.page_id, overwrite=True)
        self.props: BasicPagePropertyStack = self._update_props.props
        self.props.update_read(parsed_page.props)

        self._append_blocks = AppendBlockChildren(self.page_id, edit_mode=blocks_edit_mode)
        self.blocks = self._append_blocks.children

    @classmethod
    def from_direct_retrieve(cls, page_id) -> BasicPageEditor:
        response = RetrievePage(page_id).execute()
        parsed_page = PageProperty.from_retrieve_response(response)
        return cls(parsed_page)

    def apply(self):
        return [self._update_props.apply(), self._append_blocks.apply()]

    def execute(self):
        return [self._update_props.execute(), self._append_blocks.execute()]


class TabularPageEditor(BasicPageEditor):
    def __init__(self, parsed_page: PageProperty, parent_id='',
                 props_overwrite=DEFAULT_OVERWRITE,
                 blocks_edit_mode=DEFAULT_EDIT_MODE):
        super().__init__(parsed_page, parent_id=parent_id, blocks_edit_mode=blocks_edit_mode)
        self._update_props = UpdateTabularPage(self.page_id, overwrite=props_overwrite)
        self.props = self._update_props.props
        self.props.update_read(parsed_page.props)

    @classmethod
    def from_direct_retrieve(cls, page_id) -> TabularPageEditor:
        response = RetrievePage(page_id).execute()
        parsed_page = PageProperty.from_retrieve_response(response)
        return cls(parsed_page)


class PageListEditor:
    editor_unit = TabularPageEditor

    def __init__(self, parsed_query: PagePropertyList, database_id: str):
        self.database_id = database_id
        self.values = [self.editor_unit(parsed_page, database_id)
                       for parsed_page in parsed_query.values]
        self.page_by_id: dict[str, TabularPageEditor] \
            = {page.page_id: page for page in self.values}
        self._id_by_unique_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    @classmethod
    def from_query(cls, query: Query):
        response = query.execute()
        database_id = query.page_id
        parsed_query = PagePropertyList.from_query_response(response)
        return cls(parsed_query, database_id)

    @classmethod
    def from_query_and_retrieve_of_each_elements(cls, query: Query):
        self = cls.from_query(query)
        request_queue = []
        result_queue = []
        for page in self.values:
            request_queue.append(GetBlockChildren(page.page_id))
        for request in request_queue:
            page_id = request.block_id
            result_queue.append([page_id, request.execute()])
        for result in result_queue:
            page_id, response = result
            page = self.page_by_id[page_id]
            parsed_blocklist = BlockChildren.from_response(response)
            page.blocks.update_read(parsed_blocklist.children)
        return self

    def apply(self):
        result = []
        for page_object in self.values:
            if page_object:
                result.append(page_object.apply())
        return result

    def execute(self):
        result = []
        for page_object in self.values:
            res = page_object.execute()
            if res:
                result.append(res)
        return result

    @property
    def id_by_unique_title(self) -> dict[dict]:
        if self._id_by_unique_title is None:
            self._id_by_unique_title = {page_object.title: page_object.page_id
                                        for page_object in self.values}
        return self._id_by_unique_title

    def id_by_index(self, prop_name) -> dict[dict]:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props.read[prop_name]: page_object.page_id
                       for page_object in self.values}
            except TypeError:
                try:
                    res = {page_object.props.read[prop_name][0]: page_object.page_id
                           for page_object in self.values}
                except TypeError:
                    page_object = self.values[0]
                    pprint(f"key : {page_object.props.read[prop_name]}")
                    pprint(f"value : {page_object.page_id}")
                    raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name]

    def ids_by_prop(self, prop_name) -> dict[list[dict]]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self.values:
                res[page_object.props.read[prop_name]].append(page_object.page_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name]

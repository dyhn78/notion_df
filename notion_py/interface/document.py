from collections import defaultdict
from pprint import pprint

from notion_py.interface.parse import PageProperty, PagePropertyList
from notion_py.interface.query import Query
from notion_py.interface.write import UpdateRequest, UpdateunderDatabase
from notion_py.interface.retrieve import PageRetrieve


class PageDocument:
    def __init__(self, page_parser: PageProperty, parent_id=''):
        self.page_id = page_parser.page_id
        if parent_id:
            self.parent_id = parent_id
        else:
            self.parent_id = page_parser.parent_id
        self.title = page_parser.title

        if page_parser.parent_is_database:
            self._requestor = UpdateunderDatabase(self.page_id)
        else:
            self._requestor = UpdateRequest.under_page(self.page_id)
        self.props = self._requestor.props
        self.props.read = page_parser.props

    @classmethod
    def from_page_retrieve(cls, page_id):
        response = PageRetrieve(page_id).execute()
        page_parser = PageProperty.from_retrieve_response(response)
        return cls(page_parser)

    def apply(self):
        return self._requestor.apply()

    def execute(self):
        return self._requestor.execute()


class PageListDocument:
    def __init__(self, page_list_parser: PagePropertyList, database_id: str):
        self.database_id = database_id
        self.page_list = [PageDocument(page_parser)
                          for page_parser in page_list_parser.parser_list]

        self.page_by_id = {page.page_id: page for page in self.page_list}
        self._id_by_unique_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    @classmethod
    def from_database_query(cls, query: Query):
        response = query.execute()
        database_id = query.page_id
        page_list_parser = PagePropertyList.from_query_response(response)
        return cls(page_list_parser, database_id)

    def apply(self):
        result = []
        for page_object in self.page_list:
            if page_object:
                result.append(page_object.apply())
        return result

    def execute(self):
        result = []
        for page_object in self.page_list:
            res = page_object.execute()
            if res:
                result.append(res)
        return result

    @property
    def id_by_unique_title(self) -> dict[dict]:
        if self._id_by_unique_title is None:
            self._id_by_unique_title = {page_object.title: page_object.page_id
                                        for page_object in self.page_list}
        return self._id_by_unique_title

    def id_by_index(self, prop_name) -> dict[dict]:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props.read[prop_name]: page_object.page_id
                       for page_object in self.page_list}
            except TypeError:
                try:
                    res = {page_object.props.read[prop_name][0]: page_object.page_id
                           for page_object in self.page_list}
                except TypeError:
                    page_object = self.page_list[0]
                    pprint(f"key : {page_object.props.read[prop_name]}")
                    pprint(f"value : {page_object.page_id}")
                    raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name]

    def ids_by_prop(self, prop_name) -> dict[list[dict]]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self.page_list:
                res[page_object.props.read[prop_name]].append(page_object.page_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name]

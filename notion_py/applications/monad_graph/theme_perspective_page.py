from __future__ import annotations

from notion_py.interface.editor import TabularPage, PageList
from notion_py.interface.read import Query
from ..constants import ID_THEMES, ID_PERSPECTIVES


class ThemePage(TabularPage):
    def __init__(self, parsed_page, parent_id):
        super().__init__(parsed_page, parent_id)

    PROP_NAME = {
        'hi_themes': '✖️구성',
        'in_themes': '➖속성',
        'in_ideas': '📉속성',
        'out_themes': '➕적용',
        'lo_themes': '➗요소',
        'lo_ideas': '📉요소'
    }


class PerspectivePage(TabularPage):
    def __init__(self, parsed_page, parent_id):
        super().__init__(parsed_page, parent_id)

    PROP_NAME = {
        'hi_themes': '📈구성',
        'hi_ideas': '✖️구성',
        'in_ideas': '➖속성',
        'out_themes': '📈적용',
        'out_ideas': '➕적용',
        'lo_ideas': '➗요소',
    }


class RelationFocusedPageList(PageList):
    unit_class: type(TabularPage)
    client_id: str

    @classmethod
    def query_all(cls, page_size=0):
        query = Query(cls.client_id)
        return cls.query(query, page_size=page_size)

    def relations(self, page, relation: str):
        res = []
        for page_id in page.props.read[page.PROP_NAME[relation]]:
            try:
                res.append(self.page_by_id[page_id])
            except KeyError:
                continue
        return res


class ThemePageList(RelationFocusedPageList):
    unit_class = ThemePage
    client_id = ID_THEMES

    def __init__(self, parsed_query, parent_id):
        super().__init__(parsed_query, parent_id)
        self.values: list[ThemePage] \
            = [self.unit_class(parsed_page, parent_id)
               for parsed_page in parsed_query.values]
        self.page_by_id: dict[str, ThemePage] \
            = {page.page_id: page for page in self.values}

    @classmethod
    def query_all(cls, page_size=0) -> ThemePageList:
        return super().query_all(page_size=page_size)

    def relations(self, page: ThemePage, relation: str) -> list[ThemePage]:
        # noinspection PyTypeChecker
        return super().relations(page, relation)


class PerspectivePageList(RelationFocusedPageList):
    unit_class = PerspectivePage
    client_id = ID_PERSPECTIVES

    def __init__(self, parsed_query, parent_id):
        super().__init__(parsed_query, parent_id)
        self.values: list[PerspectivePage] \
            = [self.unit_class(parsed_page, parent_id)
               for parsed_page in parsed_query.values]
        self.page_by_id: dict[str, PerspectivePage] \
            = {page.page_id: page for page in self.values}

    @classmethod
    def query_all(cls, page_size=0) -> PerspectivePageList:
        return super().query_all(page_size=page_size)

    def relations(self, page: PerspectivePage, relation: str) -> list[PerspectivePage]:
        # noinspection PyTypeChecker
        return super().relations(page, relation)

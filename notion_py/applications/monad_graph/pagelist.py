from __future__ import annotations

from notion_py.interface.editor import TabularPage, PageList
from notion_py.interface.read import Query
from ..constants import ID_THEMES, ID_IDEAS


class SelfRelatedDataFrame:
    def __init__(self, database_id: str,
                 self_relating_flag: str,
                 prop_name: dict[str, str],
                 unit=TabularPage):
        self.database_id = database_id
        self.self_relating_flag = self_relating_flag
        self.downward_flags = ['out', 'lo']
        self.prop_name = prop_name
        self.spheres = [(key, key.split('_')[1]) for key in prop_name.keys()
                        if any(downward_flag in key for downward_flag in self.downward_flags)]
        self.unit = unit

    def query(self, page_size=0):
        query = Query(self.database_id)
        cls = SelfRelatedPageList.query_this(query, page_size=page_size, unit=self.unit)
        cls.frame = self
        # TODO / frame을 외부에서 집어넣도록 하는 이 더러운 부분 빨리 수정좀.
        return cls


class SelfRelatedPageList(PageList):
    def pages_related(self, page: type(TabularPage), prop_name: str):
        res = []
        for page_id in page.props.read[self.frame.prop_name[prop_name]]:
            try:
                res.append(self.page_by_id(page_id))
            except KeyError:
                continue
        return res


THEME_PROP_NAME = {
    'hi_themes': '✖️구성',
    'in_themes': '➖속성',
    'in_ideas': '📉속성',
    'out_themes': '➕적용',
    'lo_themes': '➗요소',
    'lo_ideas': '📉요소'
}
ThemeDatabase = SelfRelatedDataFrame(ID_THEMES, 'themes', THEME_PROP_NAME)

IDEA_PROP_NAME = {
    'hi_themes': '📈구성',
    'hi_ideas': '✖️구성',
    'in_ideas': '➖속성',
    'out_themes': '📈적용',
    'out_ideas': '➕적용',
    'lo_ideas': '➗요소',
}
IdeaDatabase = SelfRelatedDataFrame(ID_IDEAS, 'ideas', IDEA_PROP_NAME)

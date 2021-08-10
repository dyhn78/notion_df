from __future__ import annotations
from itertools import chain

from notion_py.interface.editor import TabularPage, PageList
from ..constants import ID_THEMES, ID_IDEAS
from ...interface.editor import DataFrame
from ...interface.parse import PageListParser


class SelfRelatedDataFrame(DataFrame):
    def __init__(self, database_id: str, database_name: str,
                 prop_name: dict[str, str], unit=TabularPage):
        super().__init__(database_id, database_name, prop_name, unit)
        self.downwards = \
            [(key, key.split('_')[1]) for key in prop_name.keys()
             if any(flag in key for flag in self.edge_directions['down'])]
        self.upwards = \
            [(key, key.split('_')[1]) for key in prop_name.keys()
             if any(flag in key for flag in self.edge_directions['up'])]

    @staticmethod
    def _pagelist():
        return SelfRelatedPageList

    edge_directions = {
        'down': ['lo', 'out'],
        'up': ['hi', 'in']
    }
    edge_weigths = {
        'lo': 1,
        'out': 0.4,
        'hi': 1,
        'in': 0.4
    }


class SelfRelatedPageList(PageList):
    def __init__(self, dataframe: SelfRelatedDataFrame,
                 parsed_query: PageListParser, unit=TabularPage):
        super().__init__(dataframe, parsed_query, unit)
        assert isinstance(self.dataframe, SelfRelatedDataFrame)

    def pages_related(self, page: type(TabularPage), prop_name: str):
        res = []
        for page_id in page.props.read[self.dataframe.props[prop_name].name]:
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
theme_dataframe = SelfRelatedDataFrame(ID_THEMES, 'themes', THEME_PROP_NAME)

IDEA_PROP_NAME = {
    'hi_themes': '📈구성',
    'hi_ideas': '✖️구성',
    'in_ideas': '➖속성',
    'out_themes': '📈적용',
    'out_ideas': '➕적용',
    'lo_ideas': '➗요소',
}
idea_dataframe = SelfRelatedDataFrame(ID_IDEAS, 'ideas', IDEA_PROP_NAME)

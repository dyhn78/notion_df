from __future__ import annotations
from ..constants import ID_THEMES, ID_IDEAS
from notion_py.interface.deprecated import \
    DatabaseFrameDeprecated, PageListDeprecated, TabularPageDeprecated


class SelfRelatedDatabaseFrameDeprecated(DatabaseFrameDeprecated):
    def __init__(self, database_id: str, database_name: str,
                 prop_name: dict[str, str], unit=TabularPageDeprecated):
        super().__init__(database_id, database_name, prop_name, unit)
        self.upward_keys = \
            [(key, self.get_flag(key)) for key in prop_name
             if any(flag in key for flag in self.edge_directions['up'])]
        self.downward_keys = \
            [(key, self.get_flag(key)) for key in prop_name
             if any(flag in key for flag in self.edge_directions['down'])]

    edge_directions = {
        'up': ['hi', 'out'],
        'down': ['lo', 'in'],
    }
    edge_weights = {
        'hi': 'strong',
        'lo': 'strong',
        'out': 'weak',
        'in': 'weak',
    }

    @staticmethod
    def _pagelist():
        return SelfRelatedPageListDeprecated

    @staticmethod
    def get_flag(key: str):
        return key.split('_')[1]

    @classmethod
    def parse_edge_type(cls, relation_type: str):
        weight = cls.edge_weights
        return weight[relation_type.split('_')[0]]


class SelfRelatedPageListDeprecated(PageListDeprecated):
    def __init__(self, dataframe: SelfRelatedDatabaseFrameDeprecated,
                 query_response: dict):
        super().__init__(query_response, dataframe)
        assert isinstance(self.frame, SelfRelatedDatabaseFrameDeprecated)

    def pages_related(self, alien_page: TabularPageDeprecated,
                      alien_pagelist: SelfRelatedPageListDeprecated, prop_name: str):
        res = []
        # TODO > 이 명령을 직관적으로 만드는 것이 TabularPage에 DataFrame을 이식할 때
        #  꼭 구현해야 할 점이다.
        for page_id in alien_page.props.reads[
            alien_pagelist.frame.frame[prop_name].name]:
            try:
                res.append(self.page_by_id(page_id))
            except KeyError:
                # if not res:
                #    from notion_py.utility import page_id_to_url
                #    print(alien_page.title, prop_name, page_id_to_url(page_id))
                continue
        return res


THEME_PROP_NAME = {
    'hi_themes': '✖️구성',
    'out_themes': '➕합류',
    'in_themes': '➖분기',
    'lo_themes': '➗요소',

    'hi_ideas': '📕구성',
    'in_ideas': '📕속성',
}
theme_dataframe = SelfRelatedDatabaseFrameDeprecated(ID_THEMES, 'themes', THEME_PROP_NAME)

IDEA_PROP_NAME = {
    'hi_ideas': '✖️구성',
    'out_ideas': '➕적용',
    'in_ideas': '➖속성',
    'lo_ideas': '➗요소',

    'out_themes': '📕적용',
    'lo_themes': '📕요소',
}
idea_dataframe = SelfRelatedDatabaseFrameDeprecated(ID_IDEAS, 'ideas', IDEA_PROP_NAME)

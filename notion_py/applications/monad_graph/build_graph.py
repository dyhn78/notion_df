import re
from itertools import chain

import networkx as nx

from notion_py.applications.monad_graph.self_related_dataframe \
    import SelfRelatedPageList, SelfRelatedDataFrame, theme_dataframe, idea_dataframe


class BuildGraph:
    def __init__(self, page_size: int):
        self.themes = theme_dataframe.execute_query(page_size=page_size)
        self.ideas = idea_dataframe.execute_query(page_size=page_size)
        self.all: dict[str, SelfRelatedPageList] \
            = {pagelist.dataframe.database_name: pagelist
               for pagelist in [self.themes, self.ideas]}
        self.G = nx.DiGraph()

    def execute(self):
        self.add_nodes()
        self.add_edges()
        return self.G

    def add_nodes(self):
        for i, page in enumerate(chain(*self.all.values())):
            self.G.add_node(self.parse_title(page.title), page_id=page.page_id)

    def add_edges(self):
        for down_pagelist in self.all.values():
            assert isinstance(down_pagelist.dataframe, SelfRelatedDataFrame)
            for down_page in down_pagelist:
                for upward_relation, pl_flag in down_pagelist.dataframe.upward_keys:
                    up_pagelist = self.all[pl_flag]
                    for up_page in up_pagelist.pages_related(
                            down_page, down_pagelist, upward_relation):
                        self.G.add_edge(
                            self.parse_title(down_page.title),
                            self.parse_title(up_page.title),
                            relation_type=upward_relation
                        )

    @staticmethod
    def parse_title(page_title: str):
        code = re.compile('(?<=\[).+(?=\])')  # ex) '[cdit.html_css] ....'
        if flag := code.search(page_title):
            return flag.group()
        return page_title

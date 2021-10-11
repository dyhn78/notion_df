import re
from itertools import chain
import networkx as nx

from notion_py.interface import RootEditor, TypeName
from ..database_info import DatabaseInfo
from .frame import NetworkFrames, NetworkPropertyFrame


class BuildGraph:
    def __init__(self):
        self.root = RootEditor()
        self.themes = self.root.open_pagelist(*DatabaseInfo.THEMES,
                                              NetworkFrames.THEMES)
        self.ideas = self.root.open_pagelist(*DatabaseInfo.IDEAS,
                                             NetworkFrames.IDEAS)
        self.all: dict[str, TypeName.pagelist] = \
            {pagelist.master_name: pagelist
             for pagelist in [self.themes, self.ideas]}
        self.G = nx.DiGraph()

    def execute(self, request_size=0):
        self.make_query(request_size)
        self.add_nodes()
        self.add_edges()
        return self.G

    def make_query(self, request_size):
        for pagelist in self.all.values():
            pagelist.run_query(request_size)

    def add_nodes(self):
        for i, page in enumerate(chain(*self.all.values())):
            self.G.add_node(self.parse_title(page.title), page_id=page.page_id)

    @staticmethod
    def parse_title(page_title: str):
        code = re.compile('(?<=\[).+(?=\])')  # ex) '[cdit.html_css] ....'
        if flag := code.search(page_title):
            return flag.group()
        return page_title

    def add_edges(self):
        for down_pagelist in self.all.values():
            for down_page in down_pagelist:
                down_frame = down_pagelist.frame
                assert isinstance(down_frame, NetworkPropertyFrame)
                for unit in down_frame.filter_tags('up'):
                    up_ids = down_page.props.read_at(unit.prop_tag)
                    for up_id in up_ids:
                        if up_id not in self.root.ids():
                            continue
                        up_page = self.root.by_id[up_id]
                        self.G.add_edge(
                            self.parse_title(down_page.master_name),
                            self.parse_title(up_page.master_name),
                            edge_type=unit.edge_type,
                            edge_weight=unit.edge_weight,
                        )
                # for unit in down_frame.filter_tags('up'):
                #     up_pagelist = self.all[unit.edge_target]
                #     up_ids = down_page.props.read_at(unit.prop_tag)
                #     for up_id in up_ids:
                #         if up_id not in up_pagelist.ids():
                #             continue
                #         up_page = up_pagelist.by_id[up_id]
                #         self.G.add_edge(
                #             self.parse_title(down_page.title),
                #             self.parse_title(up_page.title),
                #             edge_type=unit.edge_type,
                #             edge_weight=unit.edge_weight,
                #         )

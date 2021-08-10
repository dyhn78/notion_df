import math
from itertools import chain

import networkx as nx

from notion_py.applications.monad_graph.dataframe \
    import SelfRelatedPageList, SelfRelatedDataFrame, theme_dataframe, idea_dataframe
from notion_py.applications.monad_graph.optimize_position \
    import GradientDescent


class BuildGraph:
    def __init__(self, page_size: int):
        self.themes = theme_dataframe.execute_query(page_size=page_size)
        self.ideas = idea_dataframe.execute_query(page_size=page_size)
        self.all: dict[str, SelfRelatedPageList] \
            = {pagelist.dataframe.database_name: pagelist
               for pagelist in [self.themes, self.ideas]}
        self.graph = nx.DiGraph()

    def execute(self):
        self.add_nodes()
        self.add_edges()
        self.initialize_node_positions()
        return self.graph

    def add_nodes(self):
        for i, page in enumerate(chain(*self.all.values())):
            self.graph.add_node(page.title, page_id=page.page_id)

    def add_edges(self):
        for lead_pl in self.all.values():
            assert isinstance(lead_pl.dataframe, SelfRelatedDataFrame)
            for relation_type, pl_flag in lead_pl.dataframe.edge_directions['up']:
                follow_pl = self.all[pl_flag]
                assert isinstance(follow_pl, SelfRelatedPageList)
                for leader_page in lead_pl:
                    for follower_page in follow_pl.pages_related(
                            leader_page, relation_type):
                        self.graph.add_edge(
                            follower_page.title, leader_page.title,
                            relation_type=relation_type
                        )

    def initialize_node_positions(self):
        length = sum(len(pagelist) for pagelist in self.all.values())
        for i, page in enumerate(chain(*self.all.values())):
            theta = (2 * math.pi / length) * i
            pos = [math.cos(theta), math.sin(theta)]
            self.graph.nodes[page.title].update(pos=pos)

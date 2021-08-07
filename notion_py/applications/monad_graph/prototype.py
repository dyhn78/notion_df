from itertools import chain
import math

import networkx as nx
import plotly.graph_objects as go

from notion_py.applications.monad_graph.pagelist \
    import ThemeDatabase, IdeaDatabase, SelfRelatedPageList
from notion_py.interface.editor import PageList


class MonadList:
    def __init__(self, page_size=0):
        self.themes = ThemeDatabase.query(page_size=page_size)
        self.ideas = IdeaDatabase.query(page_size=page_size)
        self.all: dict[str, SelfRelatedPageList] \
            = {pagelist.frame.self_relating_flag: pagelist
               for pagelist in [self.themes, self.ideas]}
        self.graph = nx.DiGraph()
        self.fig = go.Figure()
        self.node_info = node_info(self.graph)

    def execute(self):
        self.assign_node_positions()
        self.add_edges()
        self.draw_graph()
        print(self.fig)
        self.fig.update_layout(showlegend=False)
        self.fig.show()

    def assign_node_positions(self):
        length = sum(len(pagelist) for pagelist in self.all.values())
        for i, page in enumerate(chain(*self.all.values())):
            theta = (2 * math.pi / length) * i
            pos = [math.cos(theta), math.sin(theta)]
            self.graph.add_node(page.title, page_id=page.page_id, pos=pos)

    def add_edges(self):
        for lead_pl in self.all.values():
            assert isinstance(lead_pl, PageList)
            for prop, pl_flag in lead_pl.frame.spheres:
                follow_pl = self.all[pl_flag]
                assert isinstance(follow_pl, PageList)
                for leader_page in lead_pl:
                    for follower_page in follow_pl.pages_related(leader_page, prop):
                        self.graph.add_edge(follower_page.title, leader_page.title)

    def draw_graph(self):
        # TODO > 'hoverinfo': 'text'
        for key_node in self.graph.nodes:
            trace = {'x': [],
                     'y': [],
                     'text': [],
                     'mode': 'lines+markers+text',
                     'textposition': 'bottom center'}
            ky = self.node_info(key_node)
            trace['x'].append(ky.x)
            trace['y'].append(ky.y)
            trace['text'].append(ky.name)
            for follow_node in self.graph.successors(key_node):
                fo = self.node_info(follow_node)
                trace['x'].extend([None, fo.x, ky.x])
                trace['y'].extend([None, fo.y, ky.y])
            self.fig.add_trace(go.Scatter(**trace))

    def draw_graph_one_by_one(self):
        for node in self.graph.nodes:
            nd = self.node_info(node)
            self.fig.add_trace(go.Scatter(
                x=[nd.x],
                y=[nd.y],
                mode='markers+text',
                text=[nd.name],
                textposition="bottom center"
            ))
        for edge in self.graph.edges:
            lo_name, hi_name = edge[0], edge[1]
            lo = self.node_info(lo_name)
            hi = self.node_info(hi_name)
            self.fig.add_trace(go.Scatter(
                x=[lo.x, hi.x],
                y=[lo.y, hi.y]
            ))


def node_info(graph: nx.DiGraph):
    class NodeInfo:
        def __init__(self, node_name: str):
            self.node = graph.nodes[node_name]
            print(node_name, self.node)
            self.x, self.y = self.node['pos']
            self.name = node_name

    return NodeInfo


if __name__ == '__main__':
    monad_list = MonadList(page_size=20)
    monad_list.execute()

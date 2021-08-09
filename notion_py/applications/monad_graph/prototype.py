from itertools import chain
import math

import networkx as nx
import plotly.graph_objects as go

from notion_py.helpers import stopwatch
from notion_py.applications.monad_graph.dataframe \
    import SelfRelatedPageList, SelfRelatedDataFrame, theme_dataframe, idea_dataframe
from notion_py.applications.monad_graph.gradient_descent \
    import GradientDescent


class MonadList:
    def __init__(self, page_size=50, epochs=5000, learning_rate=0.05):
        self.themes = theme_dataframe.execute_query(page_size=page_size)
        self.ideas = idea_dataframe.execute_query(page_size=page_size)
        self.all: dict[str, SelfRelatedPageList] \
            = {pagelist.dataframe.database_name: pagelist
               for pagelist in [self.themes, self.ideas]}
        self.graph = nx.DiGraph()
        self.fig = go.Figure()
        self.node_info = node_info(self.graph)

        self.epochs = epochs
        self.learning_rate = learning_rate

    def execute(self):
        self.add_nodes()
        self.add_edges()
        self.initialize_node_positions()
        try:
            self.optimize_node_positions()
        except KeyboardInterrupt:
            pass
        self.draw_figure()
        # print(self.fig)
        self.fig.update_layout(showlegend=False)
        self.fig.show()

    def add_nodes(self):
        for i, page in enumerate(chain(*self.all.values())):
            self.graph.add_node(page.title, page_id=page.page_id)

    def add_edges(self):
        for lead_pl in self.all.values():
            assert isinstance(lead_pl.dataframe, SelfRelatedDataFrame)
            for relation_type, pl_flag in lead_pl.dataframe.spheres:
                follow_pl = self.all[pl_flag]
                assert isinstance(follow_pl, SelfRelatedPageList)
                for leader_page in lead_pl:
                    for follower_page in follow_pl.pages_related(
                            leader_page, relation_type):
                        self.graph.add_edge(
                            leader_page.title, follower_page.title,
                            relation_type=relation_type
                        )

    def initialize_node_positions(self):
        length = sum(len(pagelist) for pagelist in self.all.values())
        for i, page in enumerate(chain(*self.all.values())):
            theta = (2 * math.pi / length) * i
            pos = [math.cos(theta), math.sin(theta)]
            self.graph.nodes[page.title].update(pos=pos)

    def optimize_node_positions(self):
        gradient_descent = GradientDescent(
            self.graph, epochs=self.epochs, learning_rate=self.learning_rate)
        gradient_descent.execute()

    def draw_figure(self):
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

    def draw_figure_prototype(self):
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
            self.x, self.y = self.node['pos']
            self.name = node_name

    return NodeInfo


if __name__ == '__main__':
    monad_list = MonadList()
    monad_list.execute()
    stopwatch('작업 완료')

import networkx as nx
from plotly import graph_objects as go

from .struct import GraphHandler


class FigureDrawer(GraphHandler):
    def __init__(self, graph: nx.DiGraph):
        super().__init__(graph)
        self.fig = go.Figure()

    def execute(self):
        self.draw_figure()
        self.fig.update_layout(showlegend=False)
        self.fig.show()
        return self.fig

    def draw_figure(self):
        # TODO > 'hoverinfo': 'text'
        for lead_node in self.G.nodes:
            trace = self.make_trace(dash=False)
            self.add_itself(trace, lead_node)
            self.add_followers_to(trace, lead_node, 'strong')
            self.fig.add_trace(go.Scatter(**trace))

            trace = self.make_trace(dash=True)
            self.add_followers_to(trace, lead_node, 'weak')
            self.fig.add_trace(go.Scatter(**trace))

    @staticmethod
    def make_trace(dash=False):
        line_type = 'dash' if dash else 'solid'
        trace = {'x': [],
                 'y': [],
                 'text': [],
                 'mode': 'lines+markers+text',
                 'line': {'dash': line_type},
                 'textposition': 'bottom center'}
        return trace

    def add_itself(self, trace, lead_node: str):
        pos = self.get_pos(lead_node)
        trace['text'].append(lead_node)
        trace['x'].append(pos.x)
        trace['y'].append(pos.y)

    def add_followers_to(self, trace, lead_node: str, edge_weight: str):
        lpos = self.get_pos(lead_node)
        for follow_node in self.G.successors(lead_node):
            if self.G.edges[lead_node, follow_node]['edge_weight'] == edge_weight:
                fpos = self.get_pos(follow_node)
                trace['x'].extend([None, fpos.x, lpos.x])
                trace['y'].extend([None, fpos.y, lpos.y])

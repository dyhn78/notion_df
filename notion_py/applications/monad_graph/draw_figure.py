import networkx as nx
from plotly import graph_objects as go


class DrawFigure:
    def __init__(self, graph: nx.DiGraph):
        self.G = graph
        self.fig = go.Figure()

    def execute(self):
        self.draw_figure()
        self.fig.update_layout(showlegend=False)
        self.fig.show()
        return self.fig

    @property
    def node_info(self):
        graph = self.G

        class NodeInfo:
            def __init__(self, node_name: str):
                self.node = graph.nodes[node_name]
                self.x, self.y = self.node['pos']
                self.name = node_name

        return NodeInfo

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
        ky = self.node_info(lead_node)
        trace['x'].apply_contents(ky.x)
        trace['y'].apply_contents(ky.y)
        trace['text'].apply_contents(ky.name)

    def add_followers_to(self, trace, lead_node: str, edge_weight: str):
        ky = self.node_info(lead_node)
        for follow_node in self.G.predecessors(lead_node):
            if self.G.edges[follow_node, lead_node]['edge_weight'] == edge_weight:
                fo = self.node_info(follow_node)
                trace['x'].extend([None, fo.x, ky.x])
                trace['y'].extend([None, fo.y, ky.y])

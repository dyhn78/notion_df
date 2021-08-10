import networkx as nx
from plotly import graph_objects as go


class DrawGraph:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.fig = go.Figure()

    def execute(self):
        self.draw_figure()
        self.show_figure()
        return self.fig

    def show_figure(self):
        self.fig.update_layout(showlegend=False)
        self.fig.show()

    @property
    def node_info(self):
        graph = self.graph

        class NodeInfo:
            def __init__(self, node_name: str):
                self.node = graph.nodes[node_name]
                self.x, self.y = self.node['pos']
                self.name = node_name

        return NodeInfo

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
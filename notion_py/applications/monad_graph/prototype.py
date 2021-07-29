import networkx as nx
import plotly.graph_objects as go
import math
# from pprint import pprint
from networkx import DiGraph

from notion_py.applications.monad_graph.theme_perspective_page \
    import ThemePageList  # , PerspectivePageList


class MonadList:
    def __init__(self, page_size=0):
        self.themes = ThemePageList.query_all(page_size=page_size)
        # self.perspectives = PerspectivePageList.query_all()

    def basic_graph(self):
        graph = nx.DiGraph()
        length = len(self.themes)
        for i, theme in enumerate(self.themes):
            theta = (2 * math.pi / length) * i
            pos = [math.cos(theta), math.sin(theta)]
            graph.add_node(theme.title, page_id=theme.page_id, pos=pos)
        for theme in self.themes:
            for hi_theme in self.themes.relations(theme, 'hi_themes'):
                graph.add_edge(theme.title, hi_theme.title)
        draw_graph(graph)


def draw_graph(graph: DiGraph):
    node_x = []
    node_y = []
    for node in graph.nodes():
        x, y = graph.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
    node_trace = go.Scatter(x=node_x, y=node_y)

    edge_x = []
    edge_y = []
    for edge in graph.edges:
        x0, y0 = graph.nodes[edge[0]]['pos']
        x1, y1 = graph.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
    edge_trace = go.Scatter(x=edge_x, y=edge_y)

    fig = go.Figure(data=[edge_trace, node_trace])
    print(fig)
    fig.show()


if __name__ == '__main__':
    monad_list = MonadList(page_size=30)
    monad_list.basic_graph()

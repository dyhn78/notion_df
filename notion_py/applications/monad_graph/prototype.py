import networkx as nx
import plotly.graph_objects as go
import math

from notion_py.applications.monad_graph.theme_perspective_page \
    import ThemePageList  # , PerspectivePageList


class MonadList:
    def __init__(self, page_size=0):
        self.graph = nx.DiGraph()
        self.themes = ThemePageList.query(page_size=page_size)
        # self.perspectives = PerspectivePageList.query_all()

    def execute(self):
        self.assign_positions()
        self.draw_graph()

    def assign_positions(self):
        length = len(self.themes)
        for i, theme in enumerate(self.themes):
            theta = (2 * math.pi / length) * i
            pos = [math.cos(theta), math.sin(theta)]
            self.graph.add_node(theme.title, page_id=theme.page_id, pos=pos)
        for theme in self.themes:
            for hi_theme in self.themes.related_pages(theme, 'hi_themes'):
                self.graph.add_edge(theme.title, hi_theme.title)

    def draw_graph(self):
        class NodeInfo:
            def __init__(self, graph: nx.DiGraph, node_name: str):
                self.node = graph.nodes[node_name]
                self.x, self.y = self.node['pos']
                self.name = f"'node_name'"

        fig = go.Figure()
        for edge in self.graph.edges:
            lo_name, hi_name = edge[0], edge[1]
            lo = NodeInfo(self.graph, lo_name)
            hi = NodeInfo(self.graph, hi_name)
            fig.add_trace(go.Scatter(
                x=[lo.x, hi.x],
                y=[lo.y, hi.y],
                text=[lo.name, hi.name]
            ))
        print(fig)
        fig.show()


if __name__ == '__main__':
    monad_list = MonadList(page_size=30)
    monad_list.execute()

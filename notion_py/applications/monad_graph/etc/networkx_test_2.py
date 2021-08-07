import networkx as nx
import matplotlib.pyplot as plt

from notion_py.applications.monad_graph.pagelist import ThemePageList, IdeaPageList


class MonadList:
    def __init__(self, page_size=0):
        self.themes = ThemePageList.query(page_size=page_size)
        # self.ideas = IdeaPageList.query_all()

    def basic_graph(self):
        graph = nx.DiGraph()
        for theme in self.themes:
            # graph.add_node(theme.title, page_id=theme.page_id)
            print(theme.title)
        for theme in self.themes:
            for hi_theme in theme.props.read[theme.PROP_NAME['hi_themes']]:
                graph.add_edge(theme.title, hi_theme.title)
        nx.draw(graph, with_labels=False)
        plt.show()


if __name__ == '__main__':
    monad_list = MonadList(page_size=0)
    monad_list.basic_graph()

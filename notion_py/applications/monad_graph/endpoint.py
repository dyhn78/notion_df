from notion_py.applications.monad_graph.common.add_nodes import TopologyBuilder
from notion_py.applications.monad_graph.graph_handler.initalize import \
    DualCircularInitializer
from notion_py.applications.monad_graph.graph_handler.positioning \
    import GradientDescent
from notion_py.applications.monad_graph.graph_handler.draw_figure import FigureDrawer
from notion_py.interface import stopwatch


class MonadGraphHandler:
    request_size = 500
    epochs_each = 1000
    mid_views = 5
    mid_stopwatchs = 5

    def execute(self):
        try:
            self._execute()
        except KeyboardInterrupt:
            pass
        stopwatch('작업 완료')

    def _execute(self):
        topology_builder = TopologyBuilder(request_size=self.request_size)
        graph = topology_builder.execute()
        subgps = DualCircularInitializer(graph).execute()
        position_handler = GradientDescent(graph, subgps,
                                           epochs=self.epochs_each * self.mid_views,
                                           mid_views=self.mid_views,
                                           mid_stopwatchs=self.mid_stopwatchs)
        graph_gen = position_handler.execute()
        for graph in graph_gen:
            FigureDrawer(graph).execute()

    def timeit(self):
        from timeit import timeit
        topology_builder = TopologyBuilder(request_size=self.request_size)
        graph = topology_builder.execute()
        subgps = DualCircularInitializer(graph).execute()
        position_handler = GradientDescent(graph, subgps,
                                           epochs=self.epochs_each * self.mid_views,
                                           mid_views=self.mid_views,
                                           mid_stopwatchs=self.mid_stopwatchs)
        print(timeit(lambda: position_handler.apply_pair_attractions(), number=50))
        print(timeit(lambda: position_handler.apply_pair_repulsions(), number=50))
        # print(timeit(lambda: position_handler.apply_uniform_shrink(), number=50))


if __name__ == '__main__':
    handler = MonadGraphHandler()
    handler.execute()
    handler.timeit()

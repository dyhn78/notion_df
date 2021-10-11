from notion_py.interface.utility import stopwatch
from notion_py.applications.monad_graph.build_graph import BuildGraph
from notion_py.applications.monad_graph.optimize_position import GradientDescent, \
    InitializeGraph
from notion_py.applications.monad_graph.draw_figure import DrawFigure

if __name__ == '__main__':
    REQUEST_SIZE = 500
    EPOCHS = 20000
    VIEWS = 5
    STOPWATCHS = 5
    LEARNING_RATE = 0.015

    build_monad_graph = BuildGraph()
    graph = build_monad_graph.execute(request_size=REQUEST_SIZE)

    # print_edges(graph)
    # print_pages(build_monad_graph)

    initialize_graph = InitializeGraph(graph)
    graph = initialize_graph.execute()

    try:
        for _ in range(VIEWS):
            optimize_position = GradientDescent(
                graph, epochs=EPOCHS // VIEWS, learning_rate=LEARNING_RATE)
            graph = optimize_position.execute(stopwatchs=STOPWATCHS)
            draw_monad_graph = DrawFigure(graph)
            figure = draw_monad_graph.execute()
    except KeyboardInterrupt:
        pass

    stopwatch('작업 완료')

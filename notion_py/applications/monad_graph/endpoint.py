from pprint import pprint

from notion_py.interface.utility import stopwatch
from notion_py.applications.monad_graph.build_graph import BuildGraph
from notion_py.applications.monad_graph.optimize_position import GradientDescent, \
    InitializeGraph
from notion_py.applications.monad_graph.draw_figure import DrawFigure


def print_nodes(gp):
    for node in gp.nodes:
        pos = gp.nodes[node]["pos"]
        pprint(f'{node}:: {round(pos[0], 3), round(pos[1], 3)}')
        pprint(list(gp.successors(node)))


def print_edges(gp):
    edges = list(gp.edges)
    edges = [(a, b) for b, a in edges]
    edges.sort()
    for a, b in edges:
        print(f'{a} <- {b}')


def print_pages(builder: BuildGraph):
    for pagelist in builder.all.values():
        for page in pagelist.values:
            pprint(page.props.read_list)


if __name__ == '__main__':
    build_monad_graph = BuildGraph(page_size=0)
    graph = build_monad_graph.execute()

    # print_edges(graph)
    # print_pages(build_monad_graph)

    initialize_graph = InitializeGraph(graph)
    graph = initialize_graph.execute()

    EPOCHS = 10000
    VIEWS = 5
    try:
        for _ in range(VIEWS):
            optimize_position = GradientDescent(
                graph, epochs=EPOCHS // VIEWS, learning_rate=0.015)
            graph = optimize_position.execute(stopwatchs=5)
            draw_monad_graph = DrawFigure(graph)
            figure = draw_monad_graph.execute()
    except KeyboardInterrupt:
        pass

    stopwatch('작업 완료')


"""
print(round(optimize_position.attraction_min, 3))
print(round(optimize_position.repulsion_max, 3))
"""
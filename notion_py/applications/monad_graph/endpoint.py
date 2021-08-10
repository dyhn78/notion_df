from pprint import pprint

from notion_py.helpers import stopwatch
from notion_py.applications.monad_graph.build_graph import BuildGraph
from notion_py.applications.monad_graph.optimize_position import GradientDescent
from notion_py.applications.monad_graph.draw_graph import DrawGraph


def print_nodes(gp):
    for node in gp.nodes:
        pos = gp.nodes[node]["pos"]
        pprint(f'{node}:: {round(pos[0], 3), round(pos[1], 3)}')
        pprint(list(gp.successors(node)))
        # print(figure)
        # print(graph.nodes)
        # print(graph.successors('대학 수업'))


if __name__ == '__main__':
    build_monad_graph = BuildGraph(page_size=0)
    graph = build_monad_graph.execute()

    optimize_position = GradientDescent(
        graph, epochs=5000, learning_rate=0.02)
    try:
        graph = optimize_position.execute()
    except KeyboardInterrupt:
        pass

    draw_monad_graph = DrawGraph(graph)
    figure = draw_monad_graph.execute()

    print(round(optimize_position.attraction_min, 3))
    print(round(optimize_position.repulsion_max, 3))
    # print_nodes(graph)

    stopwatch('작업 완료')

from pprint import pprint

from notion_py.applications.monad_graph.build_graph import BuildGraph


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
            pprint(page.props.reads)


"""
print(round(optimize_position.attraction_min, 3))
print(round(optimize_position.repulsion_max, 3))
"""
from pprint import pprint

from notion_py.applications.monad_graph.common.add_nodes import TopologyBuilder


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


def print_pages(builder: TopologyBuilder):
    for pagelist in builder.all.values():
        for page in pagelist:
            pprint(page.props.reads)

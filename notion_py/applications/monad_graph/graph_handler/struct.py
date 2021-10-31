from __future__ import annotations

import networkx as nx


class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self._dx = 0
        self._dy = 0

    def __str__(self):
        return f"<x: {self.x}, y: {self.y}, dx: {self.dx}, dy: {self.dy}>"

    def apply_changes(self):
        self.x += self.dx
        self.y += self.dy
        self.dx = self.dy = 0

    def __add__(self, p: Point):
        res = Point(self.x + p.x, self.y + p.y)
        res.dx = self.dx + p.dx
        res.dy = self.dy + p.dy
        return res

    @property
    def dx(self):
        return self._dx

    @dx.setter
    def dx(self, value):
        if type(value) not in (int, float):
            raise TypeError(value)
        if abs(value) > 1000:
            raise ValueError(value)
        self._dx = value

    @property
    def dy(self):
        return self._dy

    @dy.setter
    def dy(self, value):
        if type(value) not in (int, float):
            raise TypeError
        self._dy = value

    @property
    def r(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    @property
    def cos(self):
        try:
            return self.x / self.r
        except ZeroDivisionError:
            return 1

    @property
    def sin(self):
        try:
            return self.y / self.r
        except ZeroDivisionError:
            return 0


class GraphHandler:
    def __init__(self, graph: nx.DiGraph):
        self.G = graph

    @property
    def graph_size(self):
        number_of_nodes = len(self.G)
        return max(10, number_of_nodes) ** 0.3

    def get_node(self, node: str):
        if type(node) != str:
            raise TypeError(node)
        nd = self.G.nodes[node]
        return nd

    def get_pos(self, node: str) -> Point:
        return self.get_node(node)['pos']

    def get_dist(self, node1: str, node2: str):
        pos1 = self.get_pos(node1)
        pos2 = self.get_pos(node2)
        try:
            return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5
        except OverflowError:
            raise OverflowError(str(pos1), str(pos2))

    def get_dir(self, node1: str, node2: str):
        pos1 = self.get_pos(node1)
        pos2 = self.get_pos(node2)
        dist = self.get_dist(node1, node2)
        cos = (pos1.x - pos2.x) / dist
        sin = (pos1.y - pos2.y) / dist
        return cos, sin

    def get_edge(self, edge: tuple[str, str]):
        ed = self.G.edges[edge]
        return ed

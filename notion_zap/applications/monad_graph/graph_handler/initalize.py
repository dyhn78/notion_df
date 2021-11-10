import math

import networkx as nx

from .struct import GraphHandler, Point


class DualCircularInitializer(GraphHandler):
    def execute(self):
        large_radius = self.graph_size
        start = 0
        subgps = list(nx.connected_components(nx.Graph(self.G)))
        subgps = sorted(subgps, key=len)
        res = []
        for subgp in subgps:
            diameter = large_radius * (2 * math.pi / len(self.G)) * len(subgp)
            radius = diameter / 2

            end = start + diameter
            mid = start + radius  # argument at large circle
            pos_center = Point(large_radius * math.cos(mid),
                               large_radius * math.sin(mid))
            res.append((pos_center, subgp))

            # noinspection PyTypeChecker
            for i, node in enumerate(subgp):
                theta = (2 * math.pi / len(subgp)) * i  # argument at small circle
                pos_relative = Point(radius * math.cos(theta),
                                     radius * math.sin(theta))
                pos = pos_center + pos_relative
                self.G.nodes[node].update(pos=pos)

            start = end
        return res


class CircularInitializer(GraphHandler):
    def execute(self):
        length = self.G.number_of_nodes()
        for i, node in self.G.nodes:
            theta = (2 * math.pi / length) * i
            pos = Point(math.cos(theta), math.sin(theta))
            self.G.nodes[node].update(pos=pos)

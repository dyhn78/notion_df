# import numpy
import math

import networkx as nx
from random import random

from notion_py.utility import stopwatch
from .self_related_dataframe import SelfRelatedDatabaseFrameDeprecated


def get_dist(pos1: tuple[float, float], pos2: tuple[float, float]):
    x1, y1 = pos1
    x2, y2 = pos2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def base_density(number_of_nodes: int):
    density = 1 / (max(10, number_of_nodes) ** 0.3)
    return density


class GradientDescent:
    def __init__(self, graph: nx.DiGraph, epochs: int, learning_rate: float):
        self.G = graph
        self.epochs = epochs
        self.learning_rate = learning_rate

        self.edge_weights = {
            'strong': 1,
            'weak': 0.4
        }
        density = base_density(len(self.G))
        self.attraction_min = 0.5 * density
        self.repulsion_max = 3 * density
        self.parents_mass_when_attracting = 2
        self.parents_mass_when_repulsing = 10

        self.constant_interaction = False
        # these constants are relative to learning_rate
        self.repulsion_strength = 0.2
        self.distraction_strength = 0.05

    def execute(self, stopwatchs=10):
        for node in self.G.nodes:
            self.G.nodes[node]['dpos'] = [0, 0]
        for epoch in range(self.epochs):
            if epoch % 5 == 0:
                self.add_distraction()
            self.learning_unit()
            if epoch % max(10, self.epochs // stopwatchs) == 0:
                stopwatch(f'{epoch}회 최적화')
        return self.G

    def add_distraction(self):
        for node in self.G.nodes:
            nd = self.G.nodes[node]
            amplitude = self.learning_rate * self.distraction_strength
            dx = (2 * random() - 1) * amplitude
            dy = (2 * random() - 1) * amplitude
            nd['pos'][0] += dx
            nd['pos'][1] += dy

    def learning_unit(self):
        self.add_attraction()
        self.add_repulsion()
        self.apply_position_changes()

    def add_attraction(self):
        for edge_name in self.G.edges:
            relation_type = self.G.edges[edge_name]['relation_type']
            edge_weight = self.edge_weights[
                SelfRelatedDatabaseFrameDeprecated.parse_edge_type(relation_type)]
            self.add_attraction_between(edge_name[0], edge_name[1], edge_weight)

    def add_attraction_between(self, hi_node: str, lo_node: str, edge_weight):
        hi = self.G.nodes[hi_node]
        lo = self.G.nodes[lo_node]
        weight_hi = 1 / (1 + self.parents_mass_when_attracting)
        weight_lo = 1 - weight_hi

        dist = get_dist(hi['pos'], lo['pos'])
        if dist < self.attraction_min or dist == 0:
            return 0.

        if self.constant_interaction:
            rate = edge_weight * self.learning_rate
        else:
            rate = (edge_weight * self.learning_rate *
                    (dist - self.attraction_min) / dist)
        hi_x, hi_y = hi['pos']
        lo_x, lo_y = lo['pos']
        hi_dx = -(weight_hi * rate) * (hi_x - lo_x) / dist
        hi_dy = -(weight_hi * rate) * (hi_y - lo_y) / dist
        lo_dx = -(weight_lo * rate) * (lo_x - hi_x) / dist
        lo_dy = -(weight_lo * rate) * (lo_y - hi_y) / dist
        hi['dpos'][0] += hi_dx
        hi['dpos'][1] += hi_dy
        lo['dpos'][0] += lo_dx
        lo['dpos'][1] += lo_dy
        return rate

    def add_repulsion(self):
        for parent in self.G.nodes:
            children = list(self.G.successors(parent))
            for child1 in children:
                for child2 in children:
                    if child1 == child2:
                        continue
                    self.add_repulsion_between(child1, child2, 1)

            for child in children:
                grandchildren = list(self.G.successors(child))
                for grandchild in grandchildren:
                    self.add_repulsion_between(
                        parent, grandchild, self.parents_mass_when_repulsing)

                    for child2 in children:
                        if child == child2:
                            continue
                        self.add_repulsion_between(
                            child2, grandchild, self.parents_mass_when_repulsing ** 2)

                    great_grandchildren = list(self.G.successors(grandchild))
                    for great_grandchild in great_grandchildren:
                        self.add_repulsion_between(
                            parent, great_grandchild,
                            self.parents_mass_when_repulsing ** 3)

    def add_repulsion_between(self, node1: str, node2: str,
                              node1_relative_weight: float):
        nd1 = self.G.nodes[node1]
        nd2 = self.G.nodes[node2]
        weight1 = 1 / (1 + node1_relative_weight)
        weight2 = 1 - weight1

        dist = get_dist(nd1['pos'], nd2['pos'])
        if dist > self.repulsion_max or dist == 0:
            return 0.

        if self.constant_interaction:
            rate = self.learning_rate * self.repulsion_strength
        else:
            rate = (self.learning_rate * self.repulsion_strength *
                    (self.repulsion_max - dist) / self.repulsion_max)

        nd1_x, nd1_y = nd1['pos']
        nd2_x, nd2_y = nd2['pos']
        nd1_dx = (weight1 * rate) * (nd1_x - nd2_x) / dist
        nd1_dy = (weight1 * rate) * (nd1_y - nd2_y) / dist
        nd2_dx = (weight2 * rate) * (nd2_x - nd1_x) / dist
        nd2_dy = (weight2 * rate) * (nd2_y - nd1_y) / dist
        nd1['dpos'][0] += nd1_dx
        nd1['dpos'][1] += nd1_dy
        nd2['dpos'][0] += nd2_dx
        nd2['dpos'][1] += nd2_dy
        return rate

    def apply_position_changes(self):
        for node in self.G.nodes:
            nd = self.G.nodes[node]
            nd_dx, nd_dy = nd['dpos']
            nd['pos'][0] += nd_dx
            nd['pos'][1] += nd_dy
            nd['dpos'] = [0, 0]


class InitializeGraph:
    def __init__(self, graph: nx.DiGraph):
        self.G = graph

    def execute(self):
        self.put_in_circles()
        return self.G

    def put_in_circles(self):
        large_diameter = 1 / base_density(len(self.G))
        large_radius = large_diameter / 2

        start = 0
        graphs = list(nx.connected_components(nx.Graph(self.G)))
        graphs = sorted(graphs, key=len)
        for g in graphs:
            diameter = large_radius * (2 * math.pi / len(self.G)) * len(g)
            radius = diameter / 2

            end = start + diameter
            mid = start + radius  # argument at large circle
            pos_center = [large_radius * math.cos(mid),
                          large_radius * math.sin(mid)]

            # noinspection PyTypeChecker
            for i, node in enumerate(g):
                theta = (2 * math.pi / len(g)) * i  # argument at small circle
                pos_relative = [radius * math.cos(theta),
                                radius * math.sin(theta)]
                pos = [c + r for c, r in zip(pos_center, pos_relative)]
                self.G.nodes[node].update(pos=pos)

            start = end

    def put_in_circles_prototype(self):
        length = self.G.number_of_nodes()
        for i, node in self.G.nodes:
            theta = (2 * math.pi / length) * i
            pos = [math.cos(theta), math.sin(theta)]
            self.G.nodes[node].update(pos=pos)

# import numpy
import networkx as nx
from random import random

from notion_py.helpers import stopwatch
from .dataframe import SelfRelatedDataFrame


def get_edge_weight(relation: str):
    weight = SelfRelatedDataFrame.edge_weigths
    return weight[relation.split('_')[0]]


def get_dist(pos1: tuple[float, float], pos2: tuple[float, float]):
    x1, y1 = pos1
    x2, y2 = pos2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


class GradientDescent:
    def __init__(self, graph: nx.DiGraph, epochs: int, learning_rate: float):
        self.graph = graph
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.attraction_min = 3 / (self.graph.number_of_nodes() ** 0.5)
        self.repulsion_max = 3 / (self.graph.number_of_nodes() ** 0.5)
        self.repulsion_relative_strength = 2
        self.distraction_relative_strength = 0.4

    def execute(self):
        for node in self.graph.nodes:
            self.graph.nodes[node]['dpos'] = [0, 0]
        for epoch in range(self.epochs):
            if epoch % 20 == 0:
                self.add_distraction()
            self.learning_unit()
            if epoch % (self.epochs // 10) == 0:
                stopwatch(f'{epoch}회 최적화')
        return self.graph

    def learning_unit(self):
        self.add_attraction()
        self.add_repulsion()
        self.apply_position_changes()

    def add_distraction(self):
        for node in self.graph.nodes:
            nd = self.graph.nodes[node]
            rate = self.learning_rate * self.distraction_relative_strength
            dx = (2 * random() - 1) * rate
            dy = (2 * random() - 1) * rate
            nd['pos'][0] += dx
            nd['pos'][1] += dy

    def add_attraction(self):
        # attraction from parent(hi) to child(lo)
        for edge_name in self.graph.edges:
            hi = self.graph.nodes[edge_name[0]]
            lo = self.graph.nodes[edge_name[1]]
            relation_type = self.graph.edges[edge_name]['relation_type']
            weight = get_edge_weight(relation_type)
            self.add_attraction_each(hi, lo, weight)

    def add_attraction_each(self, hi, lo, weight):
        dist = get_dist(hi['pos'], lo['pos'])
        if dist < self.attraction_min:
            return
        rate = (weight * self.learning_rate * (dist - self.attraction_min) / dist)
        hi_x, hi_y = hi['pos']
        lo_x, lo_y = lo['pos']
        hi_dx = (-0.2 * rate) * (hi_x - lo_x) / dist
        hi_dy = (-0.2 * rate) * (hi_y - lo_y) / dist
        lo_dx = (-0.8 * rate) * (lo_x - hi_x) / dist
        lo_dy = (-0.8 * rate) * (lo_y - hi_y) / dist
        hi['dpos'][0] += hi_dx
        hi['dpos'][1] += hi_dy
        lo['dpos'][0] += lo_dx
        lo['dpos'][1] += lo_dy

    def add_repulsion(self):
        # repulsion between two children(lo1, lo2) with same parents(hi)
        for parent in self.graph.nodes:
            children = self.graph.successors(parent)
            for child1 in children:
                for child2 in children:
                    if child1 == child2:
                        continue
                    lo1 = self.graph.nodes[child1]
                    lo2 = self.graph.nodes[child2]
                    self.add_repulsion_each(lo1, lo2)

    def add_repulsion_each(self, lo1, lo2):
        dist = get_dist(lo1['pos'], lo2['pos'])
        if dist > self.repulsion_max:
            return
        rate = (self.learning_rate * self.repulsion_relative_strength *
                (self.repulsion_max - dist) / self.repulsion_max)
        lo1_x, lo1_y = lo1['pos']
        lo2_x, lo2_y = lo2['pos']
        lo1_dx = (0.5 * rate) * (lo1_x - lo2_x) / dist
        lo1_dy = (0.5 * rate) * (lo1_y - lo2_y) / dist
        lo2_dx, lo2_dy = -lo1_dx, -lo1_dy
        lo1['dpos'][0] += lo1_dx
        lo1['dpos'][1] += lo1_dy
        lo2['dpos'][0] += lo2_dx
        lo2['dpos'][1] += lo2_dy

    def apply_position_changes(self):
        for node in self.graph.nodes:
            nd = self.graph.nodes[node]
            nd_dx, nd_dy = nd['dpos']
            nd['pos'][0] += nd_dx
            nd['pos'][1] += nd_dy
            nd['dpos'] = [0, 0]

# import numpy
# from itertools import product
from random import random

import networkx as nx

from notion_zap.apps.network_builder.graph_handler.struct import GraphHandler, Point
from notion_zap.cli.utility import stopwatch


class GradientDescent(GraphHandler):
    learning_rate = 0.08
    distraction_cycle = 20
    shrink_cycle = 20

    # parameters relative to learning_rate
    attractive_strengths = {'strong': 1,
                            'weak': 0.4}
    repulsive_strength = 0.6
    distractive_strength = 0.002
    shrink_strength = 0.04

    def __init__(self, graph: nx.DiGraph, subgps: list[Point, nx.Graph],
                 epochs, mid_views, mid_stopwatchs=5,
                 ):
        super().__init__(graph)
        self.subgps = subgps
        self.epochs = epochs
        self.mid_views = mid_views
        self.epochs_each = self.epochs // self.mid_views
        self.stopwatch_intervals = max(10, self.epochs_each // mid_stopwatchs)

    def execute(self):
        for _ in range(self.mid_views):
            for epoch in range(self.epochs_each):
                self.add_pair_attractions()
                self.add_pair_repulsions()
                # self.add_tri_repulsions()
                if epoch % self.distraction_cycle == 0:
                    self.apply_distraction()
                # if epoch % self.shrink_cycle == 0:
                #     self.apply_uniform_shrink()
                for node in self.G.nodes:
                    self.get_pos(node).apply_changes()
                if (epoch + 1) % self.stopwatch_intervals == 0:
                    stopwatch(f'{epoch + 1}회 최적화')
            yield self.G

    def add_pair_attractions(self):
        for edge in self.G.edges:
            dr = \
                self.displace_with_lower_bound(edge[0], edge[1], x_intercept=0.1,
                                               exponent=0.5) * \
                self.get_strength_of(edge)
            self.apply_radial_displacements(edge[0], edge[1], 2., -1, dr)

    def add_pair_repulsions(self):
        # rel_mass_to_child = 7
        # rel_mass_to_grandchild = 15
        # rel_mass_to_nephew = 4
        for node in self.G.nodes:
            nodex = list(self.G.successors(node))
            for node1 in nodex:
                for node2 in nodex:
                    repulsion_range = 0.05 * (self.get_degree_of(node1)
                                              + self.get_degree_of(node2)) ** 0.5
                    dr = \
                        self.displace_with_upper_bound(
                            node1, node2, x_intercept=repulsion_range, exponent=0.5) * \
                        self.repulsive_strength
                    self.apply_radial_displacements(node1, node2, 1, +1, dr)

            nodey = list(self.G.predecessors(node))
            for node7 in nodey:
                for node8 in nodey:
                    repulsion_range = 0.35 * (self.get_degree_of(node7)
                                              + self.get_degree_of(node8)) ** 0.5
                    dr = \
                        self.displace_with_upper_bound(
                            node7, node8, repulsion_range, 0.5) * \
                        self.repulsive_strength
                    self.apply_radial_displacements(node7, node8, 1, +1, dr)

    def add_tri_repulsions(self):
        pass

    def apply_radial_displacements(
            self, node1, node2, node1_rel_mass: float, sign, dr: float):
        """strength: attraction if negative, repulsion if positive"""
        dist = self.get_dist(node1, node2)
        if node1 == node2 or dist == 0:
            return

        pos1 = self.get_pos(node1)
        pos2 = self.get_pos(node2)
        cos, sin = self.get_dir(node1, node2)
        dr = min(dr, 0.5 * dist)
        dr *= sign
        dr1 = dr / (1 + node1_rel_mass)
        dr2 = dr - dr1
        try:
            pos1.dx += dr1 * cos
            pos1.dy += dr1 * sin
            pos2.dx -= dr2 * cos
            pos2.dy -= dr2 * sin
        except ValueError:
            comment = (str(self.get_pos(node1)), str(self.get_pos(node2)),
                       f"dr: {dr}, dr1: {dr1}, dr2: {dr2}")
            raise ValueError(comment)

    def apply_distraction(self):
        amplitude = (self.graph_size * self.learning_rate * self.distractive_strength *
                     self.distraction_cycle)
        for pos_center, subgp in self.subgps:
            assert isinstance(pos_center, Point)
            dx_total = dy_total = 0
            for node in subgp:
                pos = self.get_pos(node)
                dx = (2 * random() - 1) * amplitude
                dy = (2 * random() - 1) * amplitude
                pos.dx += dx
                pos.dy += dy
                dx_total += dx
                dy_total += dy
            dx_total /= len(subgp)
            dy_total /= len(subgp)
            for node in subgp:
                pos = self.get_pos(node)
                pos.dx -= dx_total
                pos.dy -= dy_total

    def apply_uniform_shrink(self):
        shrink_speed_base = self.shrink_strength * self.shrink_cycle
        for pos_center, subgp in self.subgps:
            assert isinstance(pos_center, Point)
            shrink_speed = 1 - (1 - shrink_speed_base) ** (len(subgp) ** 0.5 - 1)
            if not (0 <= shrink_speed <= 1):
                raise ValueError(shrink_speed)
            for node in subgp:
                pos = self.get_pos(node)
                pos.dx -= shrink_speed * (pos.x - pos_center.x)
                pos.dy -= shrink_speed * (pos.y - pos_center.y)

    def get_degree_of(self, node: str):
        return len(list(self.G.successors(node))) \
               + len(list(self.G.predecessors(node)))

    def get_strength_of(self, edge):
        ed = self.get_edge(edge)
        edge_weight = ed['edge_weight']
        edge_strength = self.attractive_strengths[edge_weight]
        return edge_strength

    def displace_with_lower_bound(self, node1, node2, x_intercept, exponent=1.):
        dist = self.get_dist(node1, node2)
        rel_rate = max(0, (dist / x_intercept) ** exponent - 1)
        return rel_rate * self.learning_rate

    def displace_with_upper_bound(self, node1, node2, x_intercept, exponent=1.):
        dist = self.get_dist(node1, node2)
        rel_rate = max(0, 1 - (dist / x_intercept) ** exponent)
        return rel_rate * self.learning_rate

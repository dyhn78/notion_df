# import numpy
import networkx as nx

from notion_py.interface.utility import stopwatch


def edge_weight(relation: str):
    weight = {}
    nominal_weight = weight[relation.split('_')[0]]
    if nominal_weight == 'strong':
        return 1.0
    elif nominal_weight == 'weak':
        return 0.4
    raise KeyError


class GradientDescent:
    def __init__(self, graph: nx.DiGraph, epochs=100, learning_rate=0.03):
        self.graph = graph
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.minimum_square_dist = 0.2 / self.graph.number_of_nodes()
        print(f'miminum_dist: {self.minimum_square_dist ** 0.5}')
        self.repulsion_rate = self._repulsion_rate()
        self.interfere_count = 0

    def execute(self):
        for epoch in range(self.epochs):
            self.learning_unit()
            if epoch % 10 == 0:
                self.secure_minimal_distance()
            if epoch % (self.epochs // 10) == 0:
                stopwatch(f'{epoch}회 최적화, {self.interfere_count}회 조정')

    def learning_unit(self):
        # attraction by edges
        for edge in self.graph.edges:
            relation_type = self.graph.edges[edge]['relation_type']
            weight = edge_weight(relation_type)
            hi_x, hi_y = self.graph.nodes[edge[0]]['pos']
            lo_x, lo_y = self.graph.nodes[edge[1]]['pos']
            lo_x += (hi_x - lo_x) * weight * self.learning_rate
            lo_y += (hi_y - lo_y) * weight * self.learning_rate
            self.graph.nodes[edge[0]]['pos'] = lo_x, lo_y
            self.graph.nodes[edge[1]]['pos'] = hi_x, hi_y

    def secure_minimal_distance(self):
        # TODO > 방향을 조절하는 기능이 없다.
        # secure minimal distance, to prevent graph shrinking to point
        for node1 in self.graph.nodes:
            for node2 in self.graph.nodes:
                if node1 == node2:
                    continue
                nd1_x, nd1_y = self.graph.nodes[node1]['pos']
                nd2_x, nd2_y = self.graph.nodes[node2]['pos']
                square_dist = ((nd2_x - nd1_x) ** 2) + ((nd2_y - nd1_y) ** 2)
                if square_dist < self.minimum_square_dist:
                    self.interfere_count += 1
                    multiplier = (self.minimum_square_dist / square_dist) ** 0.5
                    nd2_x = nd1_x + (nd2_x - nd1_x) * multiplier
                    nd2_y = nd1_y + (nd2_y - nd1_y) * multiplier
                    self.graph.nodes[node2]['pos'] = nd2_x, nd2_y

    def add_constant_repulsion(self):
        for node in self.graph.nodes:
            nd_x, nd_y = self.graph.nodes[node]['pos']
            nd_x *= (1 + self.repulsion_rate)
            nd_y *= (1 + self.repulsion_rate)
            self.graph.nodes[node]['pos'] = nd_x, nd_y

    def _repulsion_rate(self):
        attraction = 0
        for edge in self.graph.edges:
            relation_type = self.graph.edges[edge]['relation_type']
            attraction += edge_weight(relation_type)
        return attraction / ((self.graph.number_of_nodes()) ** 2)

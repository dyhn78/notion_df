import networkx as nx
import matplotlib.pyplot as plt

G = nx.cubical_graph()
G.add_edge(3, 9)
G.add_edge(4, 8)
subax1 = plt.subplot(111)
nx.draw(G, with_labels=True)
plt.show()

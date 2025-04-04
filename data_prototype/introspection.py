from __future__ import annotations

from dataclasses import dataclass, field
import graphlib
from pprint import pformat

import matplotlib.pyplot as plt

from .conversion_edge import Edge, Graph
from .description import Desc


@dataclass
class VisNode:
    keys: list[str]
    coordinates: list[str]
    parents: list[VisNode] = field(default_factory=list)
    children: list[VisNode] = field(default_factory=list)
    x: int = 0
    y: int = 0

    def __eq__(self, other):
        return self.keys == other.keys and self.coordinates == other.coordinates

    def format(self):
        return pformat({k: v for k, v in zip(self.keys, self.coordinates)}, width=20)


@dataclass
class VisEdge:
    name: str
    parent: VisNode
    child: VisNode


def _position_subgraph(
    subgraph: tuple(set[str], list[Edge])
) -> tuple[list[VisNode], list[VisEdge]]:
    # Build graph
    nodes: list[VisNode] = []
    edges: list[VisEdge] = []

    q: list[dict[str, Desc]] = [e.input for e in subgraph[1]]
    explored: set[tuple[tuple[str, str], ...]] = set()
    explored.add(tuple(sorted(((k, v.coordinates) for k, v in q[0].items()))))

    for e in subgraph[1]:
        nodes.append(
            VisNode(list(e.input.keys()), [x.coordinates for x in e.input.values()])
        )

    while q:
        n = q.pop()
        vn = VisNode(list(n.keys()), [x.coordinates for x in n.values()])
        for nn in nodes:
            if vn == nn:
                vn = nn

        for e in subgraph[1]:
            # Shortcut default edges appearing all over the place
            if e.input == {} and vn.keys != []:
                continue
            if Desc.compatible(n, e.input):
                w = e.output
                vw = VisNode(list(w.keys()), [x.coordinates for x in w.values()])
                for nn in nodes:
                    if vw == nn:
                        vw = nn

                if vw not in nodes:
                    nodes.append(vw)
                    explored.add(
                        tuple(sorted(((k, v.coordinates) for k, v in w.items())))
                    )
                    q.append(w)
                if vw != vn:
                    edges.append(VisEdge(e.name, vn, vw))
                    vw.parents.append(vn)
                    vn.children.append(vw)

    # adapt graph for total ording
    def hash_node(n):
        return (tuple(n.keys), tuple(n.coordinates))

    to_graph = {hash_node(n): set() for n in nodes}
    for e in edges:
        to_graph[hash_node(e.child)] |= {hash_node(e.parent)}

    # evaluate total ordering
    topological_sorter = graphlib.TopologicalSorter(to_graph)

    # position horizontally by 1+ highest parent, vertically by 1+ highest sibling
    def get_node(n):
        for node in nodes:
            if n[0] == tuple(node.keys) and n[1] == tuple(node.coordinates):
                return node

    static_order = list(topological_sorter.static_order())

    for n in static_order:
        node = get_node(n)
        if node.parents != []:
            node.y = max(p.y for p in node.parents) + 1
    x_pos = {}
    for n in static_order:
        node = get_node(n)
        if node.y in x_pos:
            node.x = x_pos[node.y]
            x_pos[node.y] += 1.25
        else:
            x_pos[node.y] = 1.25

    return nodes, edges


def draw_graph(graph: Graph, ax=None):
    if ax is None:
        fig, ax = plt.subplots()

    origin_y = 0

    for sg in graph._subgraphs:
        nodes, edges = _position_subgraph(sg)
        # Draw nodes
        for node in nodes:
            ax.annotate(
                node.format(), (node.x, node.y + origin_y), bbox={"boxstyle": "round"}
            )

        # Draw edges
        for edge in edges:
            ax.annotate(
                "",
                (edge.child.x, edge.child.y + origin_y),
                (edge.parent.x, edge.parent.y + origin_y),
                arrowprops={"arrowstyle": "->"},
            )
            mid_x = (edge.child.x + edge.parent.x) / 2
            mid_y = (edge.child.y + edge.parent.y) / 2
            ax.text(mid_x, mid_y + origin_y, edge.name)

        origin_y += max(node.y for node in nodes) + 1

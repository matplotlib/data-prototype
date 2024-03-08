from collections.abc import Sequence
from typing import Callable
from dataclasses import dataclass
from typing import Any
import numpy as np

from data_prototype.containers import Desc

from matplotlib.transforms import Transform


@dataclass
class Edge:
    name: str
    input: dict[str, Desc]
    output: dict[str, Desc]
    invertable: bool = True

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        return input

    @property
    def inverse(self) -> "Edge":
        return Edge(self.name + "_r", self.output, self.input)


@dataclass
class SequenceEdge(Edge):
    edges: Sequence[Edge] = ()

    @classmethod
    def from_edges(cls, name: str, edges: Sequence[Edge], output: dict[str, Desc]):
        input = {}
        intermediates = {}
        invertable = True
        for edge in edges:
            input |= {k: v for k, v in edge.input.items() if k not in intermediates}
            intermediates |= edge.output
            if not edge.invertable:
                invertable = False
        return cls(name, input, output, invertable, edges)

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        for edge in self.edges:
            input |= edge.evaluate({k: input[k] for k in edge.input})
        return {k: input[k] for k in self.output}

    @property
    def inverse(self) -> "SequenceEdge":
        return SequenceEdge.from_edges(
            self.name + "_r", [e.inverse for e in self.edges[::-1]], self.input
        )


@dataclass
class FuncEdge(Edge):
    # TODO: more explicit callable boundaries?
    func: Callable = lambda: {}
    inverse_func: Callable | None = None

    @classmethod
    def from_func(
        cls,
        name: str,
        func: Callable,
        input: str | dict[str, Desc],
        output: str | dict[str, Desc],
        inverse: Callable | None = None,
    ):
        # dtype/shape is reductive here, but I like the idea of being able to just
        # supply a function and the input/output coordinates for many things
        if isinstance(input, str):
            import inspect

            input_vars = inspect.signature(func).parameters.keys()
            input = {k: Desc(("N",), np.dtype("f8"), input) for k in input_vars}
        if isinstance(output, str):
            output = {k: Desc(("N",), np.dtype("f8"), output) for k in input.keys()}

        return cls(name, input, output, inverse is not None, func, inverse)

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        res = self.func(**{k: input[k] for k in self.input})

        if isinstance(res, dict):
            # TODO: more sanity checks here?
            # How forgiving do we _really_ wish to be?
            return res
        elif isinstance(res, tuple):
            if len(res) != len(self.output):
                raise RuntimeError(
                    f"Expected {len(self.output)} return values, got {len(res)}"
                )
            return {k: v for k, v in zip(self.output, res)}
        elif len(self.output) == 1:
            return {k: res for k in self.output}
        raise RuntimeError("Output of function does not match expected output")

    @property
    def inverse(self) -> "FuncEdge":
        return FuncEdge.from_func(
            self.name + "_r", self.inverse_func, self.output, self.input, self.func
        )


@dataclass
class TransformEdge(Edge):
    transform: Transform | Callable[[], Transform] | None = None

    # TODO: helper for common cases/validation?

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        # TODO: ensure ordering?
        # Stacking and unstacking at every step seems inefficient,
        # especially if initially given as stacked
        if self.transform is None:
            return input
        elif isinstance(self.transform, Callable):
            trf = self.transform()
        else:
            trf = self.transform
        inp = np.stack([input[k] for k in self.input], axis=-1)
        outp = trf.transform(inp)
        return {k: v for k, v in zip(self.output, outp.T)}

    @property
    def inverse(self) -> "TransformEdge":
        if isinstance(self.transform, Callable):
            return TransformEdge(
                self.name + "_r",
                self.output,
                self.input,
                True,
                lambda: self.transform().inverted(),
            )

        return TransformEdge(
            self.name + "_r", self.output, self.input, True, self.transform.inverted()
        )


class Graph:
    def __init__(self, edges: Sequence[Edge]):
        self._edges = edges
        # TODO: precompute some internal representation?
        #   - Nodes between edges, potentially in discrete subgraphs
        #   - Inversions are not included right now

    def evaluator(self, input: dict[str, Desc], output: dict[str, Desc]) -> Edge:
        # May wish to solve for each output independently
        # Probably can be smarter here and prune more effectively.
        q: list[tuple[dict[str, Desc], tuple[Edge, ...]]] = [(input, ())]

        def trace(x: dict[str, Desc]) -> tuple[tuple[str, str], ...]:
            return tuple(sorted([(k, v.coordinates) for k, v in x.items()]))

        explored: set[tuple[tuple[str, str], ...]] = set()
        explored.add(trace(input))
        edges = ()
        while q:
            v, edges = q.pop()
            if Desc.compatible(v, output):
                break
            for e in self._edges:
                if Desc.compatible(v, e.input):
                    w = (v | e.output, (*edges, e))
                    w_trace = trace(w[0])
                    if w_trace in explored:
                        # This may need to be more explicitly checked...
                        # May not accurately be checking what we consider "in"
                        continue
                    explored.add(w_trace)
                    q.append(w)
        else:
            # TODO: case where non-linear solving is needed
            raise NotImplementedError(
                "This may be possible, but is not a simple case already considered"
            )
        if len(edges) == 0:
            return Edge("noop", input, output)
        elif len(edges) == 1:
            return edges[0]
        else:
            return SequenceEdge.from_edges("eval", edges, output)

    def visualize(self, input: dict[str, Desc] | None = None):
        import networkx as nx
        import matplotlib.pyplot as plt
        from pprint import pformat

        def node_format(x):
            return pformat({k: v.coordinates for k, v in x.items()})

        G = nx.DiGraph()

        if input is not None:
            q: list[dict[str, Desc]] = [input]
            explored: set[tuple[tuple[str, str], ...]] = set()
            explored.add(tuple(sorted(((k, v.coordinates) for k, v in q[0].items()))))
            G.add_node(node_format(q[0]))
            while q:
                n = q.pop()
                for e in self._edges:
                    if Desc.compatible(n, e.input):
                        w = n | e.output
                        if node_format(w) not in G:
                            G.add_node(node_format(w))
                            explored.add(
                                tuple(
                                    sorted(((k, v.coordinates) for k, v in w.items()))
                                )
                            )
                            q.append(w)
                        if node_format(w) != node_format(n):
                            G.add_edge(node_format(n), node_format(w), name=e.name)
        else:
            for edge in self._edges:
                G.add_edge(
                    node_format(edge.input), node_format(edge.output), name=edge.name
                )

        pos = nx.planar_layout(G)
        plt.figure()
        nx.draw(G, pos=pos, with_labels=True)
        nx.draw_networkx_edge_labels(G, pos=pos)
        # plt.show()

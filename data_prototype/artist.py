from bisect import insort
from typing import Sequence

import numpy as np

from .containers import DataContainer, ArrayContainer, DataUnion
from .description import Desc, desc_like
from .conversion_edge import Edge, Graph, TransformEdge


class Artist:
    required_keys: dict[str, Desc]

    # defaults?
    def __init__(
        self, container: DataContainer, edges: Sequence[Edge] | None = None, **kwargs
    ):
        kwargs_cont = ArrayContainer(**kwargs)
        self._container = DataUnion(container, kwargs_cont)

        edges = edges or []
        self._visible = True
        self._graph = Graph(edges)
        self._clip_box: DataContainer = ArrayContainer(
            {"x": "parent", "y": "parent"},
            **{"x": np.asarray([0, 1]), "y": np.asarray([0, 1])}
        )

    def draw(self, renderer, graph: Graph) -> None:
        return

    def set_clip_box(self, container: DataContainer) -> None:
        self._clip_box = container

    def get_clip_box(self, container: DataContainer) -> DataContainer:
        return self._clip_box

    def get_visible(self):
        return self._visible

    def set_visible(self, visible):
        self._visible = visible


class CompatibilityArtist:
    """A compatibility shim to ducktype as a classic Matplotlib Artist.

    At this time features are implemented on an "as needed" basis, and many
    are only implemented insofar as they do not fail, not necessarily providing
    full functionality of a full MPL Artist.

    The idea is to keep the new Artist class as minimal as possible.
    As features are added this may shrink.

    The main thing we are trying to avoid is the reliance on the axes/figure

    Ultimately for useability, whatever remains shimmed out here may be rolled in as
    some form of gaurded option to ``Artist`` itself, but a firm dividing line is
    useful for avoiding accidental dependency.
    """

    def __init__(self, artist: Artist):
        self._artist = artist

        self._axes = None
        self.figure = None
        self._clippath = None
        self._visible = True
        self.zorder = 2
        self._graph = Graph([])

    @property
    def axes(self):
        return self._axes

    @axes.setter
    def axes(self, ax):
        self._axes = ax

        if self._axes is None:
            self._graph = Graph([])
            return

        desc: Desc = Desc(("N",), coordinates="data")
        xy: dict[str, Desc] = {"x": desc, "y": desc}
        self._graph = Graph(
            [
                TransformEdge(
                    "data",
                    xy,
                    desc_like(xy, coordinates="axes"),
                    transform=self._axes.transData - self._axes.transAxes,
                ),
                TransformEdge(
                    "axes",
                    desc_like(xy, coordinates="axes"),
                    desc_like(xy, coordinates="display"),
                    transform=self._axes.transAxes,
                ),
            ],
            aliases=(("parent", "axes"),),
        )

    def set_figure(self, fig):
        self.figure = fig

    def is_transform_set(self):
        return True

    def get_mouseover(self):
        return False

    def get_clip_path(self):
        self._clippath

    def set_clip_path(self, path):
        self._clippath = path

    def get_animated(self):
        return False

    def get_visible(self):
        return self._visible

    def set_visible(self, visible):
        self._visible = visible

    def draw(self, renderer, graph=None):
        if not self.get_visible():
            return

        if graph is None:
            graph = Graph([])
        self._artist.draw(renderer, graph + self._graph)


class CompatibilityAxes:
    """A compatibility shim to add to traditional matplotlib axes.

    At this time features are implemented on an "as needed" basis, and many
    are only implemented insofar as they do not fail, not necessarily providing
    full functionality of a full MPL Artist.

    The idea is to keep the new Artist class as minimal as possible.
    As features are added this may shrink.

    The main thing we are trying to avoid is the reliance on the axes/figure

    Ultimately for useability, whatever remains shimmed out here may be rolled in as
    some form of gaurded option to ``Artist`` itself, but a firm dividing line is
    useful for avoiding accidental dependency.
    """

    def __init__(self, axes):
        self._axes = axes
        self.figure = None
        self._clippath = None
        self._visible = True
        self.zorder = 2
        self._children: list[tuple[float, Artist]] = []

    @property
    def axes(self):
        return self._axes

    @axes.setter
    def axes(self, ax):
        self._axes = ax

        if self._axes is None:
            self._graph = Graph([])
            return

        desc: Desc = Desc(("N",), coordinates="data")
        xy: dict[str, Desc] = {"x": desc, "y": desc}
        self._graph = Graph(
            [
                TransformEdge(
                    "data",
                    xy,
                    desc_like(xy, coordinates="axes"),
                    transform=self._axes.transData - self._axes.transAxes,
                ),
                TransformEdge(
                    "axes",
                    desc_like(xy, coordinates="axes"),
                    desc_like(xy, coordinates="display"),
                    transform=self._axes.transAxes,
                ),
            ],
            aliases=(("parent", "axes"),),
        )

    def set_figure(self, fig):
        self.figure = fig

    def is_transform_set(self):
        return True

    def get_mouseover(self):
        return False

    def get_clip_path(self):
        self._clippath

    def set_clip_path(self, path):
        self._clippath = path

    def get_animated(self):
        return False

    def draw(self, renderer, graph=None):
        if not self.visible:
            return
        if graph is None:
            graph = Graph([])

        graph = graph + self._graph

        for _, c in self._children:
            c.draw(renderer, graph)

    def add_artist(self, artist, zorder=1):
        insort(self._children, (zorder, artist), key=lambda x: x[0])

    def set_xlim(self, min_=None, max_=None):
        self.axes.set_xlim(min_, max_)

    def set_ylim(self, min_=None, max_=None):
        self.axes.set_ylim(min_, max_)

    def get_visible(self):
        return self._visible

    def set_visible(self, visible):
        self._visible = visible

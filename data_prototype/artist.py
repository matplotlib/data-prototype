from typing import Sequence

import numpy as np

from .containers import DataContainer, ArrayContainer, DataUnion
from .description import Desc, desc_like
from .conversion_edge import Edge, TransformEdge


class Artist:
    required_keys: dict[str, Desc]

    # defaults?
    def __init__(
        self, container: DataContainer, edges: Sequence[Edge] | None = None, **kwargs
    ):
        kwargs_cont = ArrayContainer(**kwargs)
        self._container = DataUnion(container, kwargs_cont)

        edges = edges or []
        self._edges = list(edges)

    def draw(self, renderer, edges: Sequence[Edge]) -> None:
        return


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

        self.axes = None
        self.figure = None
        self._clippath = None
        self.zorder = 2

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

    def draw(self, renderer, edges=None):

        if edges is None:
            edges = []

        if self.axes is not None:
            desc: Desc = Desc(("N",), np.dtype("f8"), coordinates="data")
            xy: dict[str, Desc] = {"x": desc, "y": desc}
            edges.append(
                TransformEdge(
                    "data",
                    xy,
                    desc_like(xy, coordinates="axes"),
                    transform=self.axes.transData - self.axes.transAxes,
                )
            )
            edges.append(
                TransformEdge(
                    "axes",
                    desc_like(xy, coordinates="axes"),
                    desc_like(xy, coordinates="display"),
                    transform=self.axes.transAxes,
                )
            )

        self._artist.draw(renderer, edges)

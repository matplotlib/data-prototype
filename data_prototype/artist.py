from bisect import insort
from collections import OrderedDict
from typing import Sequence
from contextlib import contextmanager

import numpy as np

from matplotlib.backend_bases import PickEvent
import matplotlib.artist as martist

from .containers import DataContainer, ArrayContainer, DataUnion
from .description import Desc, desc_like
from .conversion_edge import Edge, FuncEdge, Graph, TransformEdge


class Artist:
    required_keys: dict[str, Desc]

    # defaults?
    def __init__(
        self, container: DataContainer, edges: Sequence[Edge] | None = None, **kwargs
    ):
        kwargs_cont = ArrayContainer(**kwargs)
        self._container = DataUnion(container, kwargs_cont)

        self._children: list[tuple[float, Artist]] = []
        self._picker = None

        edges = edges or []
        self._visible = True
        self._graph = Graph(edges)
        self._clip_box: DataContainer = ArrayContainer(
            {"x": "parent", "y": "parent"},
            **{"x": np.asarray([0, 1]), "y": np.asarray([0, 1])}
        )

        self._caches = {}

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

    def pickable(self) -> bool:
        return self._picker is not None

    def get_picker(self):
        return self._picker

    def set_picker(self, picker):
        self._picker = picker

    def contains(self, mouseevent, graph=None):
        """
        Test whether the artist contains the mouse event.

        Parameters
        ----------
        mouseevent : `~matplotlib.backend_bases.MouseEvent`

        Returns
        -------
        contains : bool
            Whether any values are within the radius.
        details : dict
            An artist-specific dictionary of details of the event context,
            such as which points are contained in the pick radius. See the
            individual Artist subclasses for details.
        """
        return False, {}

    def get_children(self):
        return [a[1] for a in self._children]

    def pick(self, mouseevent, graph: Graph | None = None):
        """
        Process a pick event.

        Each child artist will fire a pick event if *mouseevent* is over
        the artist and the artist has picker set.

        See Also
        --------
        set_picker, get_picker, pickable
        """
        if graph is None:
            graph = self._graph
        else:
            graph = graph + self._graph
        # Pick self
        if self.pickable():
            picker = self.get_picker()
            if callable(picker):
                inside, prop = picker(self, mouseevent)
            else:
                inside, prop = self.contains(mouseevent, graph)
            if inside:
                PickEvent(
                    "pick_event", mouseevent.canvas, mouseevent, self, **prop
                )._process()

        # Pick children
        for a in self.get_children():
            # make sure the event happened in the same Axes
            ax = getattr(a, "axes", None)
            if mouseevent.inaxes is None or ax is None or mouseevent.inaxes == ax:
                # we need to check if mouseevent.inaxes is None
                # because some objects associated with an Axes (e.g., a
                # tick label) can be outside the bounding box of the
                # Axes and inaxes will be None
                # also check that ax is None so that it traverse objects
                # which do not have an axes property but children might
                a.pick(mouseevent, graph)

    def _get_dynamic_graph(self, query, description, graph, cacheset):
        return Graph([])

    def _query_and_eval(self, container, requires, graph, cacheset=None):
        g = graph + self._graph
        query, q_cache_key = container.query(g)
        g = g + self._get_dynamic_graph(query, container.describe(), graph, cacheset)
        g_cache_key = g.cache_key()
        cache_key = (g_cache_key, q_cache_key)

        cache = None
        if cacheset is not None:
            cache = self._caches.setdefault(cacheset, OrderedDict())
            if cache_key in cache:
                return cache[cache_key]

        conv = g.evaluator(container.describe(), requires)
        ret = conv.evaluate(query)

        # TODO: actually add to cache and prune
        # if cache is not None:
        #     cache[cache_key] = ret

        return ret


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

    def __init__(self, artist: martist.Artist):
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


class CompatibilityAxes(Artist):
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
        super().__init__(ArrayContainer())
        self._axes = axes
        self.figure = None
        self._clippath = None
        self.zorder = 2

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
        desc_scal: Desc = Desc((), coordinates="data")
        xy: dict[str, Desc] = {"x": desc, "y": desc}
        xy_scal: dict[str, Desc] = {"x": desc_scal, "y": desc_scal}

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
                TransformEdge(
                    "data_scal",
                    xy_scal,
                    desc_like(xy_scal, coordinates="axes"),
                    transform=self._axes.transData - self._axes.transAxes,
                ),
                TransformEdge(
                    "axes_scal",
                    desc_like(xy_scal, coordinates="axes"),
                    desc_like(xy_scal, coordinates="display"),
                    transform=self._axes.transAxes,
                ),
                FuncEdge.from_func(
                    "xunits",
                    lambda: self._axes.xaxis.units,
                    {},
                    {"xunits": Desc((), "units")},
                ),
                FuncEdge.from_func(
                    "yunits",
                    lambda: self._axes.yaxis.units,
                    {},
                    {"yunits": Desc((), "units")},
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
        if not self.get_visible():
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


@contextmanager
def _renderer_group(renderer, group, gid):
    renderer.open_group(group, gid)
    try:
        yield
    finally:
        renderer.close_group(group)

from typing import Sequence

import matplotlib.path as mpath
import matplotlib.colors as mcolors
import matplotlib.lines as mlines
import matplotlib.markers as mmarkers
import matplotlib.transforms as mtransforms
import numpy as np

from .artist import Artist
from .description import Desc
from .conversion_edge import Edge, Graph, CoordinateEdge, DefaultEdge


class Line(Artist):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        scalar = Desc((), "display")  # ... this needs thinking...

        self._edges += [
            CoordinateEdge.from_coords("xycoords", {"x": "auto", "y": "auto"}, "data"),
            CoordinateEdge.from_coords("color", {"color": Desc(())}, "display"),
            CoordinateEdge.from_coords("linewidth", {"linewidth": Desc(())}, "display"),
            CoordinateEdge.from_coords("linestyle", {"linestyle": Desc(())}, "display"),
            CoordinateEdge.from_coords(
                "markeredgecolor", {"markeredgecolor": Desc(())}, "display"
            ),
            CoordinateEdge.from_coords(
                "markerfacecolor", {"markerfacecolor": Desc(())}, "display"
            ),
            CoordinateEdge.from_coords(
                "markersize", {"markersize": Desc(())}, "display"
            ),
            CoordinateEdge.from_coords(
                "markeredgewidth", {"markeredgewidth": Desc(())}, "display"
            ),
            CoordinateEdge.from_coords("marker", {"marker": Desc(())}, "display"),
            DefaultEdge.from_default_value("color_def", "color", scalar, "C0"),
            DefaultEdge.from_default_value("linewidth_def", "linewidth", scalar, 1),
            DefaultEdge.from_default_value("linestyle_def", "linestyle", scalar, "-"),
            DefaultEdge.from_default_value("mec_def", "markeredgecolor", scalar, "C0"),
            DefaultEdge.from_default_value("mfc_def", "markerfacecolor", scalar, "C0"),
            DefaultEdge.from_default_value("ms_def", "markersize", scalar, 6),
            DefaultEdge.from_default_value("mew_def", "markeredgewidth", scalar, 1),
            DefaultEdge.from_default_value("marker_def", "marker", scalar, "None"),
        ]
        # Currently ignoring:
        # - cap/join style
        # - url
        # - antialiased
        # - snapping
        # - sketch
        # - gap color
        # - draw style (steps)
        # - fill style/alt_marker_path
        # - markevery
        # - non-str markers
        # Each individually pretty easy, but relatively rare features, focusing on common cases

    def draw(self, renderer, edges: Sequence[Edge]) -> None:
        g = Graph(list(edges) + self._edges)
        desc = Desc(("N",), "display")
        scalar = Desc((), "display")  # ... this needs thinking...

        require = {
            "x": desc,
            "y": desc,
            "color": scalar,
            "linewidth": scalar,
            "linestyle": scalar,
            "markeredgecolor": scalar,
            "markerfacecolor": scalar,
            "markersize": scalar,
            "markeredgewidth": scalar,
            "marker": scalar,
        }

        conv = g.evaluator(self._container.describe(), require)
        query, _ = self._container.query(g)
        x, y, color, lw, ls, *marker = conv.evaluate(query).values()
        mec, mfc, ms, mew, mark = marker

        # make the Path object
        path = mpath.Path(np.vstack([x, y]).T)
        # make an configure the graphic context
        gc = renderer.new_gc()
        gc.set_foreground(color)
        gc.set_linewidth(lw)
        gc.set_dashes(*mlines._scale_dashes(*mlines._get_dash_pattern(ls), lw))
        # add the line to the render buffer
        renderer.draw_path(gc, path, mtransforms.IdentityTransform())

        if mark != "None" and ms > 0:
            gc = renderer.new_gc()
            gc.set_linewidth(mew)
            gc.set_foreground(mec)
            marker_ = mmarkers.MarkerStyle(mark)
            marker_path = marker_.get_path()
            marker_trans = marker_.get_transform()
            w = renderer.points_to_pixels(ms)
            marker_trans = marker_trans.scale(w)
            mfc = mcolors.to_rgba(mfc)
            renderer.draw_markers(
                gc,
                marker_path,
                marker_trans,
                path,
                mtransforms.IdentityTransform(),
                mfc,
            )

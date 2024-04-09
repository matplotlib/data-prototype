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

        colordesc = Desc((), str, "display")  # ... this needs thinking...
        floatdesc = Desc((), float, "display")
        strdesc = Desc((), str, "display")

        self._edges += [
            CoordinateEdge.from_coords("xycoords", {"x": "auto", "y": "auto"}, "data"),
            CoordinateEdge.from_coords("color", {"color": Desc((), str)}, "display"),
            CoordinateEdge.from_coords(
                "linewidth", {"linewidth": Desc((), np.dtype("f8"))}, "display"
            ),
            CoordinateEdge.from_coords(
                "linestyle", {"linestyle": Desc((), str)}, "display"
            ),
            CoordinateEdge.from_coords(
                "markeredgecolor", {"markeredgecolor": Desc((), str)}, "display"
            ),
            CoordinateEdge.from_coords(
                "markerfacecolor", {"markerfacecolor": Desc((), str)}, "display"
            ),
            CoordinateEdge.from_coords(
                "markersize", {"markersize": Desc((), float)}, "display"
            ),
            CoordinateEdge.from_coords(
                "markeredgewidth", {"markeredgewidth": Desc((), float)}, "display"
            ),
            CoordinateEdge.from_coords("marker", {"marker": Desc((), str)}, "display"),
            DefaultEdge.from_default_value("color_def", "color", colordesc, "C0"),
            DefaultEdge.from_default_value("linewidth_def", "linewidth", floatdesc, 1),
            DefaultEdge.from_default_value("linestyle_def", "linestyle", strdesc, "-"),
            DefaultEdge.from_default_value(
                "mec_def", "markeredgecolor", colordesc, "C0"
            ),
            DefaultEdge.from_default_value(
                "mfc_def", "markerfacecolor", colordesc, "C0"
            ),
            DefaultEdge.from_default_value("ms_def", "markersize", floatdesc, 6),
            DefaultEdge.from_default_value("mew_def", "markeredgewidth", floatdesc, 1),
            DefaultEdge.from_default_value("marker_def", "marker", strdesc, "None"),
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
        desc = Desc(("N",), np.dtype("f8"), "display")
        colordesc = Desc((), str, "display")  # ... this needs thinking...
        floatdesc = Desc((), float, "display")
        strdesc = Desc((), str, "display")

        require = {
            "x": desc,
            "y": desc,
            "color": colordesc,
            "linewidth": floatdesc,
            "linestyle": strdesc,
            "markeredgecolor": colordesc,
            "markerfacecolor": colordesc,
            "markersize": floatdesc,
            "markeredgewidth": floatdesc,
            "marker": strdesc,
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

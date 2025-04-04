import matplotlib.path as mpath
import matplotlib.colors as mcolors
import matplotlib.lines as mlines
import matplotlib.markers as mmarkers
import matplotlib.transforms as mtransforms
import numpy as np

from .artist import Artist
from .description import Desc
from .conversion_edge import Graph, CoordinateEdge, DefaultEdge

segment_hits = mlines.segment_hits


class Line(Artist):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        scalar = Desc((), "display")  # ... this needs thinking...

        default_edges = [
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
        self._graph = self._graph + Graph(default_edges)
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

    def contains(self, mouseevent, graph=None):
        """
        Test whether *mouseevent* occurred on the line.

        An event is deemed to have occurred "on" the line if it is less
        than ``self.pickradius`` (default: 5 points) away from it.  Use
        `~.Line2D.get_pickradius` or `~.Line2D.set_pickradius` to get or set
        the pick radius.

        Parameters
        ----------
        mouseevent : `~matplotlib.backend_bases.MouseEvent`

        Returns
        -------
        contains : bool
            Whether any values are within the radius.
        details : dict
            A dictionary ``{'ind': pointlist}``, where *pointlist* is a
            list of points of the line that are within the pickradius around
            the event position.

            TODO: sort returned indices by distance
        """
        if graph is None:
            return False, {}

        g = graph + self._graph
        desc = Desc(("N",), "display")
        scalar = Desc((), "display")  # ... this needs thinking...
        # Convert points to pixels
        require = {
            "x": desc,
            "y": desc,
            "linestyle": scalar,
        }
        conv = g.evaluator(self._container.describe(), require)
        query, _ = self._container.query(g)
        xt, yt, linestyle = conv.evaluate(query).values()

        # Convert pick radius from points to pixels
        pixels = 5  # self._pickradius # TODO

        # The math involved in checking for containment (here and inside of
        # segment_hits) assumes that it is OK to overflow, so temporarily set
        # the error flags accordingly.
        with np.errstate(all="ignore"):
            # Check for collision
            if linestyle in ["None", None]:
                # If no line, return the nearby point(s)
                (ind,) = np.nonzero(
                    (xt - mouseevent.x) ** 2 + (yt - mouseevent.y) ** 2 <= pixels**2
                )
            else:
                # If line, return the nearby segment(s)
                ind = segment_hits(mouseevent.x, mouseevent.y, xt, yt, pixels)
                # if self._drawstyle.startswith("steps"):
                #    ind //= 2

        # Return the point(s) within radius
        return len(ind) > 0, dict(ind=ind)

    def draw(self, renderer, graph: Graph) -> None:
        if not self.get_visible():
            return
        g = graph + self._graph
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

        clip_conv = g.evaluator(
            self._clip_box.describe(),
            {"x": Desc(("N",), "display"), "y": Desc(("N",), "display")},
        )
        clip_query, _ = self._clip_box.query(g)
        clipx, clipy = clip_conv.evaluate(clip_query).values()

        # make the Path object
        path = mpath.Path(np.vstack([x, y]).T)
        # make an configure the graphic context
        gc = renderer.new_gc()
        gc.set_clip_rectangle(
            mtransforms.Bbox.from_extents(clipx[0], clipy[0], clipx[1], clipy[1])
        )
        gc.set_foreground(color)
        gc.set_linewidth(lw)
        gc.set_dashes(*mlines._scale_dashes(*mlines._get_dash_pattern(ls), lw))
        # add the line to the render buffer
        renderer.draw_path(gc, path, mtransforms.IdentityTransform())

        if mark != "None" and ms > 0:
            gc = renderer.new_gc()
            gc.set_clip_rectangle(
                mtransforms.Bbox.from_extents(clipx[0], clipy[0], clipx[1], clipy[1])
            )
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

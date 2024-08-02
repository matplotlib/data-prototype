import numpy as np

from matplotlib.font_manager import FontProperties

from .artist import Artist
from .description import Desc
from .conversion_edge import Graph, CoordinateEdge, coord_and_default


class Text(Artist):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        edges = [
            CoordinateEdge.from_coords(
                "xycoords", {"x": Desc((), "auto"), "y": Desc((), "auto")}, "data"
            ),
            *coord_and_default("text", default_value=""),
            *coord_and_default("color", default_rc="text.color"),
            *coord_and_default("alpha", default_value=1),
            *coord_and_default("fontproperties", default_value=FontProperties()),
            *coord_and_default("usetex", default_rc="text.usetex"),
            *coord_and_default("rotation", default_value=0),
            *coord_and_default("antialiased", default_rc="text.antialiased"),
        ]

        self._graph = self._graph + Graph(edges)

    def draw(self, renderer, graph: Graph) -> None:
        if not self.get_visible():
            return
        g = graph + self._graph
        conv = g.evaluator(
            self._container.describe(),
            {
                "x": Desc((), "display"),
                "y": Desc((), "display"),
                "text": Desc((), "display"),
                "color": Desc((), "display"),
                "alpha": Desc((), "display"),
                "fontproperties": Desc((), "display"),
                "usetex": Desc((), "display"),
                # "parse_math": Desc((), "display"),
                # "wrap": Desc((), "display"),
                # "verticalalignment": Desc((), "display"),
                # "horizontalalignment": Desc((), "display"),
                "rotation": Desc((), "display"),
                # "linespacing": Desc((), "display"),
                # "rotation_mode": Desc((), "display"),
                "antialiased": Desc((), "display"),
            },
        )

        query, _ = self._container.query(g)
        evald = conv.evaluate(query)

        text = evald["text"]
        if text == "":
            return

        x = evald["x"]
        y = evald["y"]

        _, canvash = renderer.get_canvas_width_height()
        if renderer.flipy():
            y = canvash - y

        if not np.isfinite(x) or not np.isfinite(y):
            # TODO: log?
            return

        # TODO bbox?
        # TODO implement wrapping/layout?
        # TODO implement math?
        # TODO implement path_effects?

        # TODO gid?
        renderer.open_group("text", None)

        gc = renderer.new_gc()
        gc.set_foreground(evald["color"])
        gc.set_alpha(evald["alpha"])
        # TODO url?
        gc.set_antialiased(evald["antialiased"])
        # TODO clipping?

        if evald["usetex"]:
            renderer.draw_tex(
                gc, x, y, text, evald["fontproperties"], evald["rotation"]
            )
        else:
            renderer.draw_text(
                gc, x, y, text, evald["fontproperties"], evald["rotation"]
            )

        gc.restore()
        renderer.close_group("text")

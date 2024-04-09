from typing import Sequence

import matplotlib.cm as mcm
import matplotlib.colors as mcolors
import matplotlib.transforms as mtransforms
import numpy as np

from .artist import Artist
from .description import Desc, desc_like
from .conversion_edge import Edge, FuncEdge, Graph, CoordinateEdge, DefaultEdge


class Image(Artist):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        strdesc = Desc((), str)
        arrdesc = Desc(("M", "N"), np.float64)
        normdesc = Desc((), mcolors.Normalize, "norm")
        cmapdesc = Desc((), mcolors.Colormap, "cmap")

        self._edges += [
            CoordinateEdge.from_coords(
                "A_pcolor", {"A": Desc(("M", "N"), np.float64)}, "data"
            ),
            CoordinateEdge.from_coords(
                "A_rgb", {"A": Desc(("M", "N", 3), np.float64)}, "rgb"
            ),
            CoordinateEdge.from_coords(
                "A_rgba", {"A": Desc(("M", "N", 4), np.float64)}, "rgba"
            ),
            FuncEdge.from_func(
                "norm_obj",
                lambda norm: mcm._auto_norm_from_scale(norm),
                {"norm": desc_like(strdesc, coordinates="norm")},
                {"norm": normdesc},
            ),
            FuncEdge.from_func(
                "cmap_obj",
                lambda cmap: mcm._colormaps[cmap],
                {"cmap": desc_like(strdesc, coordinates="cmap")},
                {"cmap": cmapdesc},
            ),
            FuncEdge.from_func(
                "A_norm",
                lambda A, norm: norm(A),
                {"A": desc_like(arrdesc), "norm": normdesc},
                {"A": desc_like(arrdesc, coordinates="norm")},
            ),
            FuncEdge.from_func(
                "A_cmap",
                lambda A, cmap: cmap(A),
                {"A": desc_like(arrdesc, coordinates="norm"), "cmap": cmapdesc},
                {"A": Desc(("M", "N", 4), np.float64, coordinates="rgba")},
            ),
            DefaultEdge.from_default_value("cmap_def", "cmap", strdesc, "viridis"),
            DefaultEdge.from_default_value("norm_def", "norm", strdesc, "linear"),
            CoordinateEdge.from_coords(
                "A_rgba", {"A": Desc(("M", "N", 4), np.float64, "rgba")}, "display"
            ),
        ]

    def draw(self, renderer, edges: Sequence[Edge]) -> None:
        import matplotlib.pyplot as plt

        g = Graph(list(edges) + self._edges)
        g.visualize()
        plt.show()
        conv = g.evaluator(
            self._container.describe(),
            {"A": Desc(("M", "N", 4), np.float64, "display")},
        )
        query, _ = self._container.query(g)
        image = conv.evaluate(query)["A"]

        gc = renderer.new_gc()
        renderer.draw_image(gc, image, mtransforms.IdentityTransform())
        ...

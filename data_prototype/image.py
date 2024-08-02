import numpy as np

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.transforms as mtransforms

from .artist import Artist
from .description import Desc, desc_like
from .conversion_edge import FuncEdge, Graph, CoordinateEdge


def _interpolate_nearest(image, x, y):
    magnification = 1  # TODO
    lef, rig = x
    width = int(((round(rig) + 0.5) - (round(lef) - 0.5)) * magnification)

    xpix = np.digitize(np.arange(width), np.linspace(0, rig - lef, image.shape[1]))

    bot, top = y
    height = int(((round(top) + 0.5) - (round(bot) - 0.5)) * magnification)
    ypix = np.digitize(np.arange(height), np.linspace(0, top - bot, image.shape[0]))

    out = np.empty((height, width, 4))

    out[:, :, :] = image[
        ypix[:, None].clip(0, image.shape[0] - 1),
        xpix[None, :].clip(0, image.shape[1] - 1),
        :,
    ]
    return out


class Image(Artist):
    def __init__(self, container, edges=None, norm=None, cmap=None, **kwargs):
        super().__init__(container, edges, **kwargs)
        if norm is None:
            norm = mcolors.Normalize()
        if cmap is None:
            cmap = mpl.colormaps["viridis"]
        self.norm = norm
        self.cmap = cmap

        arrdesc = Desc(("M", "N"))

        self._interpolation_edge = FuncEdge.from_func(
            "interpolate_nearest_rgba",
            _interpolate_nearest,
            {
                "image": Desc(("M", "N", 4), coordinates="rgba"),
                "x": Desc(("X",), coordinates="display"),
                "y": Desc(("Y",), coordinates="display"),
            },
            {"image": Desc(("O", "P", 4), coordinates="rgba_resampled")},
        )

        edges = [
            CoordinateEdge.from_coords("xycoords", {"x": "auto", "y": "auto"}, "data"),
            CoordinateEdge.from_coords(
                "image_coords", {"image": Desc(("M", "N"), "auto")}, "data"
            ),
            FuncEdge.from_func(
                "image_norm",
                lambda image: self.norm(image),
                {"image": desc_like(arrdesc, coordinates="data_resampled")},
                {"image": desc_like(arrdesc, coordinates="norm")},
            ),
            FuncEdge.from_func(
                "image_cmap",
                lambda image: self.cmap(image),
                {"image": desc_like(arrdesc, coordinates="norm")},
                {"image": Desc(("M", "N", 4), coordinates="rgba")},
            ),
            FuncEdge.from_func(
                "image_display",
                lambda image: (image * 255).astype(np.uint8),
                {"image": Desc(("O", "P", 4), "rgba_resampled")},
                {"image": Desc(("O", "P", 4), "display")},
            ),
            FuncEdge.from_func(
                "rgb_rgba",
                lambda image: np.append(
                    image, np.ones(image.shape[:-1] + (1,)), axis=-1
                ),
                {"image": Desc(("M", "N", 3), "rgb")},
                {"image": Desc(("M", "N", 4), "rgba")},
            ),
            self._interpolation_edge,
        ]

        self._graph = self._graph + Graph(edges, (("data", "data_resampled"),))

    def draw(self, renderer, graph: Graph) -> None:
        if not self.get_visible():
            return
        g = graph + self._graph
        conv = g.evaluator(
            self._container.describe(),
            {
                "image": Desc(("O", "P", 4), "display"),
                "x": Desc(("X",), "display"),
                "y": Desc(("Y",), "display"),
            },
        )
        query, _ = self._container.query(g)
        evald = conv.evaluate(query)
        image = evald["image"]
        x = evald["x"]
        y = evald["y"]

        clip_conv = g.evaluator(
            self._clip_box.describe(),
            {"x": Desc(("N",), "display"), "y": Desc(("N",), "display")},
        )
        clip_query, _ = self._clip_box.query(g)
        clipx, clipy = clip_conv.evaluate(clip_query).values()

        gc = renderer.new_gc()
        gc.set_clip_rectangle(
            mtransforms.Bbox.from_extents(clipx[0], clipy[0], clipx[1], clipy[1])
        )
        renderer.draw_image(gc, x[0], y[0], image)  # TODO vector backend transforms

    def contains(self, mouseevent, graph=None):
        if graph is None:
            return False, {}
        g = graph + self._graph
        conv = g.evaluator(
            self._container.describe(),
            {
                "x": Desc(("X",), "display"),
                "y": Desc(("Y",), "display"),
            },
        ).inverse
        query, _ = self._container.query(g)
        xmin, xmax = query["x"]
        ymin, ymax = query["y"]
        x, y = conv.evaluate({"x": mouseevent.x, "y": mouseevent.y}).values()

        # This checks xmin <= x <= xmax *or* xmax <= x <= xmin.
        inside = (
            x is not None
            and (x - xmin) * (x - xmax) <= 0
            and y is not None
            and (y - ymin) * (y - ymax) <= 0
        )

        return inside, {}

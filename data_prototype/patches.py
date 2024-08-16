from matplotlib.patches import Patch as _Patch, Rectangle as _Rectangle
import matplotlib.path as mpath
import matplotlib.transforms as mtransforms
import matplotlib.colors as mcolors
import numpy as np


from .wrappers import ProxyWrapper, _stale_wrapper

from .containers import DataContainer

from .artist import Artist, _renderer_group
from .description import Desc
from .conversion_edge import Graph, CoordinateEdge, DefaultEdge


class Patch(Artist):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        scalar = Desc((), "display")  # ... this needs thinking...
        edges = [
            CoordinateEdge.from_coords("xycoords", {"x": "auto", "y": "auto"}, "data"),
            CoordinateEdge.from_coords("codes", {"codes": "auto"}, "display"),
            CoordinateEdge.from_coords("facecolor", {"color": Desc(())}, "display"),
            CoordinateEdge.from_coords("edgecolor", {"color": Desc(())}, "display"),
            CoordinateEdge.from_coords("linewidth", {"linewidth": Desc(())}, "display"),
            CoordinateEdge.from_coords("hatch", {"hatch": Desc(())}, "display"),
            CoordinateEdge.from_coords("alpha", {"alpha": Desc(())}, "display"),
            DefaultEdge.from_default_value("facecolor_def", "facecolor", scalar, "C0"),
            DefaultEdge.from_default_value("edgecolor_def", "edgecolor", scalar, "C0"),
            DefaultEdge.from_default_value("linewidth_def", "linewidth", scalar, 1),
            DefaultEdge.from_default_value("linestyle_def", "linestyle", scalar, "-"),
            DefaultEdge.from_default_value("alpha_def", "alpha", scalar, 1),
            DefaultEdge.from_default_value("hatch_def", "hatch", scalar, None),
        ]
        self._graph = self._graph + Graph(edges)

    def draw(self, renderer, graph: Graph) -> None:
        if not self.get_visible():
            return
        g = graph + self._graph
        desc = Desc(("N",), "display")
        scalar = Desc((), "display")  # ... this needs thinking...

        require = {
            "x": desc,
            "y": desc,
            "codes": desc,
            "facecolor": scalar,
            "edgecolor": scalar,
            "linewidth": scalar,
            "linestyle": scalar,
            "hatch": scalar,
            "alpha": scalar,
        }

        # copy from line
        conv = g.evaluator(self._container.describe(), require)
        query, _ = self._container.query(g)
        evald = conv.evaluate(query)

        clip_conv = g.evaluator(
            self._clip_box.describe(),
            {"x": Desc(("N",), "display"), "y": Desc(("N",), "display")},
        )
        clip_query, _ = self._clip_box.query(g)
        clipx, clipy = clip_conv.evaluate(clip_query).values()
        # copy from line

        path = mpath.Path._fast_from_codes_and_verts(
            verts=np.vstack([evald["x"], evald["y"]]).T, codes=evald["codes"]
        )

        with _renderer_group(renderer, "patch", None):
            gc = renderer.new_gc()

            gc.set_foreground(evald["facecolor"], isRGBA=False)
            gc.set_clip_rectangle(
                mtransforms.Bbox.from_extents(clipx[0], clipy[0], clipx[1], clipy[1])
            )
            gc.set_linewidth(evald["linewidth"])
            # gc.set_dashes(*self._dash_pattern)
            # gc.set_capstyle(self._capstyle)
            # gc.set_joinstyle(self._joinstyle)

            # gc.set_antialiased(self._antialiased)

            # gc.set_url(self._url)
            # gc.set_snap(self.get_snap())

            gc.set_alpha(evald["alpha"])

            if evald["hatch"] is not None:
                gc.set_hatch(evald["hatch"])
                gc.set_hatch_color(evald["hatch_color"])

            # if self.get_sketch_params() is not None:
            #     gc.set_sketch_params(*self.get_sketch_params())

            # if self.get_path_effects():
            #    from matplotlib.patheffects import PathEffectRenderer
            #    renderer = PathEffectRenderer(self.get_path_effects(), renderer)

            renderer.draw_path(
                gc,
                path,
                mtransforms.IdentityTransform(),
                mcolors.to_rgba(evald["facecolor"]),
            )
            gc.restore()


class PatchWrapper(ProxyWrapper):
    _wrapped_class = _Patch
    _privtized_methods = (
        "get_edgecolor",
        "get_facecolor",
        "get_linewidth",
        "get_linestyle",
        "get_antialiased",
        "get_hatch",
        "get_fill",
        "get_capstyle",
        "get_joinstyle",
        "get_path",
        "set_edgecolor",
        "set_facecolor",
        "set_linewidth",
        "set_linestyle",
        "set_antialiased",
        "set_hatch",
        "set_fill",
        "set_capstyle",
        "set_joinstyle",
        "set_path",
    )
    required_keys = {
        "edgecolor",
        "facecolor",
        "linewidth",
        "linestyle",
        "antialiased",
        "hatch",
        "fill",
        "capstyle",
        "joinstyle",
    }

    def __init__(self, data: DataContainer, converters=None, /, **kwargs):
        super().__init__(data, converters)
        self._wrapped_instance = self._wrapped_class([0, 0], 0, 0, **kwargs)

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(self._query_and_transform(renderer))
        return self._wrapped_instance.draw(renderer)

    def _update_wrapped(self, data):
        for k, v in data.items():
            getattr(self._wrapped_instance, f"set_{k}")(v)


class RectangleWrapper(PatchWrapper):
    _wrapped_class = _Rectangle
    _privtized_methods = PatchWrapper._privtized_methods + (
        "get_x",
        "get_y",
        "get_width",
        "get_height",
        "get_angle",
        "get_rotation_point" "set_x",
        "set_y",
        "set_width",
        "set_height",
        "set_angle",
        "set_rotation_point",
    )
    required_keys = PatchWrapper.required_keys | {
        "x",
        "y",
        "width",
        "height",
        "angle",
        "rotation_point",
    }

    def _update_wrapped(self, data):
        for k, v in data.items():
            if k == "rotation_point":
                self._wrapped_instance.rotation_point = v
                continue
            # linestyle and hatch do not work as arrays,
            # but ArrayContainer requires arrays, so index into an array if needed
            elif k in ("linestyle", "hatch"):
                if isinstance(v, np.ndarray):
                    v = v[0]
            getattr(self._wrapped_instance, f"set_{k}")(v)

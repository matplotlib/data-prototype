from matplotlib.patches import Patch as _Patch, Rectangle as _Rectangle
import matplotlib.path as mpath
import matplotlib.transforms as mtransforms
import matplotlib.colors as mcolors
import numpy as np


from .wrappers import ProxyWrapper, _stale_wrapper

from .artist import Artist, _renderer_group
from .description import Desc, desc_like
from .containers import DataContainer
from .conversion_edge import Graph, CoordinateEdge, DefaultEdge, TransformEdge


class Patch(Artist):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        scalar = Desc((), "display")  # ... this needs thinking...
        def_edges = [
            CoordinateEdge.from_coords("xycoords", {"x": "auto", "y": "auto"}, "data"),
            CoordinateEdge.from_coords("codes", {"codes": "auto"}, "display"),
            CoordinateEdge.from_coords("facecolor", {"facecolor": Desc(())}, "display"),
            CoordinateEdge.from_coords("edgecolor", {"edgecolor": Desc(())}, "display"),
            CoordinateEdge.from_coords(
                "facecolor_rgba", {"facecolor": Desc(("M",))}, "display"
            ),
            CoordinateEdge.from_coords(
                "edgecolor_rgba", {"edgecolor": Desc(("M",))}, "display"
            ),
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
        self._graph = self._graph + Graph(def_edges)

    def draw(self, renderer, graph: Graph) -> None:
        if not self.get_visible():
            return
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

        evald = self._query_and_eval(
            self._container, require, graph, cacheset="default"
        )

        clip_req = {"x": Desc(("N",), "display"), "y": Desc(("N",), "display")}
        clipx, clipy = self._query_and_eval(
            self._clip_box, clip_req, graph, cacheset="clip"
        ).values()

        path = mpath.Path._fast_from_codes_and_verts(
            verts=np.vstack([evald["x"], evald["y"]]).T, codes=evald["codes"]
        )

        with _renderer_group(renderer, "patch", None):
            gc = renderer.new_gc()

            gc.set_foreground(evald["edgecolor"], isRGBA=False)
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
                # gc.set_hatch_color(evald["hatch_color"])

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


class RectangleContainer(DataContainer): ...


class Rectangle(Patch):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        rect = mpath.Path.unit_rectangle()

        desc = Desc((4,), "abstract_path")
        scalar = Desc((), "data")
        scalar_auto = Desc(())
        def_edges = [
            CoordinateEdge.from_coords(
                "llxycoords",
                {"lower_left_x": scalar_auto, "lower_left_y": scalar_auto},
                "data",
            ),
            CoordinateEdge.from_coords(
                "urxycoords",
                {"upper_right_x": scalar_auto, "upper_right_y": scalar_auto},
                "data",
            ),
            CoordinateEdge.from_coords(
                "rpxycoords",
                {"rotation_point_x": scalar_auto, "rotation_point_y": scalar_auto},
                "data",
            ),
            CoordinateEdge.from_coords("anglecoords", {"angle": scalar_auto}, "data"),
            DefaultEdge.from_default_value(
                "x_def", "x", desc, rect.vertices.T[0], weight=0.1
            ),
            DefaultEdge.from_default_value(
                "y_def", "y", desc, rect.vertices.T[1], weight=0.1
            ),
            DefaultEdge.from_default_value(
                "codes_def",
                "codes",
                desc_like(desc, coordinates="display"),
                rect.codes,
                weight=0.1,
            ),
            DefaultEdge.from_default_value("angle_def", "angle", scalar, 0),
            DefaultEdge.from_default_value(
                "rotation_point_x_def", "rotation_point_x", scalar, 0
            ),
            DefaultEdge.from_default_value(
                "rotation_point_y_def", "rotation_point_y", scalar, 0
            ),
        ]

        self._graph = self._graph + Graph(def_edges)

    def _get_dynamic_graph(self, query, description, graph, cacheset):
        if cacheset == "clip":
            return Graph([])

        desc = Desc((), "data")

        requires = {
            "upper_right_x": desc,
            "upper_right_y": desc,
            "lower_left_x": desc,
            "lower_left_y": desc,
            "angle": desc,
            "rotation_point_x": desc,
            "rotation_point_y": desc,
        }

        g = graph + self._graph

        conv = g.evaluator(description, requires)
        evald = conv.evaluate(query)

        bbox = mtransforms.Bbox.from_extents(
            evald["lower_left_x"],
            evald["lower_left_y"],
            evald["upper_right_x"],
            evald["upper_right_y"],
        )
        rotation_point = (evald["rotation_point_x"], evald["rotation_point_y"])

        scale = mtransforms.BboxTransformTo(bbox)
        rotate = (
            mtransforms.Affine2D()
            .translate(-rotation_point[0], -rotation_point[1])
            .rotate_deg(evald["angle"])
            .translate(*rotation_point)
        )

        descn: Desc = Desc(("N",), coordinates="data")
        xy: dict[str, Desc] = {"x": descn, "y": descn}
        edges = [
            TransformEdge(
                "scale_and_rotate",
                desc_like(xy, coordinates="abstract_path"),
                xy,
                transform=scale + rotate,
            )
        ]

        return Graph(edges)


class RegularPolygon(Patch):
    def __init__(self, container, edges=None, **kwargs):
        super().__init__(container, edges, **kwargs)

        scalar = Desc((), "data")
        scalar_auto = Desc(())
        def_edges = [
            CoordinateEdge.from_coords(
                "centercoords",
                {"center_x": scalar_auto, "center_y": scalar_auto},
                "data",
            ),
            CoordinateEdge.from_coords(
                "orientationcoords", {"orientation": scalar_auto}, "data"
            ),
            CoordinateEdge.from_coords("radiuscoords", {"radius": scalar_auto}, "data"),
            CoordinateEdge.from_coords(
                "num_vertices_coords", {"num_vertices": scalar_auto}, "data"
            ),
            DefaultEdge.from_default_value("orientation_def", "orientation", scalar, 0),
            DefaultEdge.from_default_value("radius_def", "radius", scalar, 5),
        ]

        self._graph = self._graph + Graph(def_edges)

    def _get_dynamic_graph(self, query, description, graph, cacheset):
        if cacheset == "clip":
            return Graph([])

        desc = Desc((), "data")
        desc_abs = Desc(("N",), "abstract_path")

        requires = {
            "center_x": desc,
            "center_y": desc,
            "radius": desc,
            "orientation": desc,
            "num_vertices": desc,
        }

        g = graph + self._graph

        conv = g.evaluator(description, requires)
        evald = conv.evaluate(query)

        circ = mpath.Path.unit_regular_polygon(evald["num_vertices"])

        scale = mtransforms.Affine2D().scale(evald["radius"])
        rotate = mtransforms.Affine2D().rotate(evald["orientation"])
        translate = mtransforms.Affine2D().translate(
            evald["center_x"], evald["center_y"]
        )

        descn: Desc = Desc(("N",), coordinates="data")
        xy: dict[str, Desc] = {"x": descn, "y": descn}
        edges = [
            TransformEdge(
                "scale_and_rotate",
                desc_like(xy, coordinates="abstract_path"),
                xy,
                transform=scale + rotate + translate,
            ),
            DefaultEdge.from_default_value(
                "x_def", "x", desc_abs, circ.vertices.T[0], weight=0.1
            ),
            DefaultEdge.from_default_value(
                "y_def", "y", desc_abs, circ.vertices.T[1], weight=0.1
            ),
            DefaultEdge.from_default_value(
                "codes_def",
                "codes",
                desc_like(desc_abs, coordinates="display"),
                circ.codes,
                weight=0.1,
            ),
        ]

        return Graph(edges)


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

from typing import Dict, Any, Protocol, Tuple, get_type_hints
import inspect

import numpy as np

from cachetools import LFUCache
from functools import partial, wraps

import matplotlib as mpl
from matplotlib.lines import Line2D as _Line2D
from matplotlib.image import AxesImage as _AxesImage
from matplotlib.patches import StepPatch as _StepPatch
from matplotlib.text import Text as _Text
import matplotlib.transforms as mtransforms
from matplotlib.collections import (
    LineCollection as _LineCollection,
    PathCollection as _PathCollection,
)
from matplotlib.artist import Artist as _Artist

from mpl_data_containers.containers import DataContainer, _MatplotlibTransform
from mpl_data_containers.description import Desc, desc_like
from mpl_data_containers.conversion_edge import TransformEdge, Graph
from mpl_data_containers.conversion_node import (
    ConversionNode,
    RenameConversionNode,
    evaluate_pipeline,
    FunctionConversionNode,
    LimitKeysConversionNode,
)


class _BBox(Protocol):
    size: Tuple[float, float]


class _Axis(Protocol):
    def convert_units(self, Any) -> Any: ...


class _Axes(Protocol):
    xaxis: _Axis
    yaxis: _Axis

    transData: _MatplotlibTransform
    transAxes: _MatplotlibTransform

    def get_xlim(self) -> Tuple[float, float]: ...

    def get_ylim(self) -> Tuple[float, float]: ...

    def get_window_extent(self, renderer) -> _BBox: ...


class _Aritst(Protocol):
    axes: _Axes


def _make_identity(k):
    def identity(**kwargs):
        (_,) = kwargs.values()
        return _

    identity.__signature__ = inspect.Signature(
        [inspect.Parameter(k, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    )
    return identity


def _forwarder(forwards, cls=None):
    if cls is None:
        return partial(_forwarder, forwards)

    def make_forward(name):
        def method(self, *args, **kwargs):
            for parent in cls.mro()[1:]:
                if hasattr(parent, name):
                    ret = getattr(parent, name)(self, *args, **kwargs)
                    break
            else:
                raise AttributeError
            for c in self.get_children():
                ret = getattr(c, name)(*args, **kwargs)
            return ret

        return method

    for f in forwards:
        method = make_forward(f)
        method.__name__ = f
        method.__doc__ = "broadcasts {} to children".format(f)
        setattr(cls, f, method)

    return cls


def _stale_wrapper(func):
    @wraps(func)
    def inner(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        finally:
            self.stale = False

    return inner


class ProxyWrapperBase:
    data: DataContainer
    axes: _Axes
    stale: bool
    required_keys: set = set()
    expected_keys: set = set()

    @_stale_wrapper
    def draw(self, renderer):
        raise NotImplementedError

    def _update_wrapped(self, data):
        raise NotImplementedError

    def _query_and_transform(self, renderer) -> Dict[str, Any]:
        """
        Helper to centralize the data querying and python-side transforms

        Parameters
        ----------
        renderer : RendererBase
        """
        # extract what we need to about the axes to query the data
        ax = self.axes

        # actually query the underlying data.  This returns both the (raw) data
        # and key to use for caching.
        desc = Desc(("N",), coordinates="data")
        xy = {"x": desc, "y": desc}
        edges = [
            TransformEdge(
                "axes",
                xy,
                desc_like(xy, coordinates="axes"),
                transform=ax.transData - ax.transAxes,
            ),
            TransformEdge(
                "axes",
                desc_like(xy, coordinates="axes"),
                desc_like(xy, coordinates="display"),
                transform=ax.transAxes,
            ),
        ]
        graph = Graph(edges)
        data, cache_key = self.data.query(graph, "axes")
        # see if we can short-circuit
        try:
            return self._cache[cache_key]
        except KeyError:
            ...
        delayed_conversion = {
            "xunits": ax.xaxis.convert_units,
            "yunits": ax.yaxis.convert_units,
        }
        transformed_data = evaluate_pipeline(self._converters, data, delayed_conversion)

        self._cache[cache_key] = transformed_data
        return transformed_data

    def __init__(
        self, data, converters: ConversionNode | list[ConversionNode] | None, **kwargs
    ):
        super().__init__(**kwargs)
        self.data = data
        self._cache = LFUCache(64)
        # TODO make sure mutating this will invalidate the cache!
        if isinstance(converters, ConversionNode):
            converters = [converters]
        self._converters: list[ConversionNode] = converters or []
        setters = list(self.expected_keys | self.required_keys)
        if hasattr(self, "_wrapped_class"):
            setters += [f[4:] for f in dir(self._wrapped_class) if f.startswith("set_")]
        self._converters.append(LimitKeysConversionNode.from_keys(setters))
        self.stale = True


class ProxyWrapper(ProxyWrapperBase):
    _privtized_methods: Tuple[str, ...] = ()
    _wrapped_class = None
    _wrapped_instance: _Aritst

    def __getattr__(self, key):
        if key in self._privtized_methods:
            raise AttributeError(f"The method {key} has been privitized")
        if key[0] == "_" and key[1:] in self._privtized_methods:
            return getattr(self._wrapped_instance, key[1:])
        return getattr(self._wrapped_instance, key)

    def __setattr__(self, key, value):
        if key in (
            "_wrapped_instance",
            "data",
            "_cache",
            "_converters",
            "stale",
            "_sigs",
        ):
            super().__setattr__(key, value)
        elif hasattr(self, "_wrapped_instance") and hasattr(
            self._wrapped_instance, key
        ):
            setattr(self._wrapped_instance, key, value)
        else:
            super().__setattr__(key, value)


class LineWrapper(ProxyWrapper):
    _wrapped_class = _Line2D
    _privtized_methods = (
        "set_xdata",
        "set_ydata",
        "set_data",
        "get_xdata",
        "get_ydata",
        "get_data",
    )
    required_keys = {"x", "y"}

    def __init__(self, data: DataContainer, converters=None, /, **kwargs):
        super().__init__(data, converters)
        self._wrapped_instance = self._wrapped_class(
            np.array([]), np.array([]), **kwargs
        )
        self._converters.insert(
            -1, RenameConversionNode.from_mapping({"x": "xdata", "y": "ydata"})
        )
        setters = [f[4:] for f in dir(self._wrapped_class) if f.startswith("set_")]
        self._converters[-1] = LimitKeysConversionNode.from_keys(setters)

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(
            self._query_and_transform(renderer),
        )
        return self._wrapped_instance.draw(renderer)

    def _update_wrapped(self, data):
        for k, v in data.items():
            getattr(self._wrapped_instance, f"set_{k}")(v)


class PathCollectionWrapper(ProxyWrapper):
    _wrapped_class = _PathCollection
    required_keys = {"x", "y", "paths", "facecolors", "edgecolors", "sizes"}
    _privtized_methods = (
        "set_facecolors",
        "set_edgecolors",
        "set_offsets",
        "set_sizes",
        "set_paths",
        "get_facecolors",
        "get_edgecolors",
        "get_offsets",
        "get_sizes",
        "get_paths",
    )

    def __init__(self, data: DataContainer, converters=None, /, **kwargs):
        super().__init__(data, converters)
        self._wrapped_instance = self._wrapped_class([], **kwargs)
        self._wrapped_instance.set_transform(mtransforms.IdentityTransform())

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(
            self._query_and_transform(renderer),
        )
        return self._wrapped_instance.draw(renderer)

    def _update_wrapped(self, data):
        self._wrapped_instance.set_offsets(np.array([data["x"], data["y"]]).T)
        self._wrapped_instance.set_paths(data["paths"])
        self._wrapped_instance.set_facecolors(data["facecolors"])
        self._wrapped_instance.set_edgecolors(data["edgecolors"])
        self._wrapped_instance.set_sizes(data["sizes"])


class ImageWrapper(ProxyWrapper):
    _wrapped_class = _AxesImage
    required_keys = {"xextent", "yextent", "image"}

    def __init__(
        self, data: DataContainer, converters=None, /, cmap=None, norm=None, **kwargs
    ):
        converters = converters or []
        if cmap is not None or norm is not None:
            if converters is not None and "image" in converters:
                raise ValueError("Conflicting input")
            if cmap is None:
                cmap = mpl.colormaps["viridis"]
            if norm is None:
                raise ValueError("not sure how to do autoscaling yet")
            converters.append(
                FunctionConversionNode.from_funcs(
                    {"image": lambda image: cmap(norm(image))}
                )
            )
        super().__init__(data, converters)
        kwargs.setdefault("origin", "lower")
        self._wrapped_instance = self._wrapped_class(None, **kwargs)

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(
            self._query_and_transform(renderer),
        )
        return self._wrapped_instance.draw(renderer)

    def _update_wrapped(self, data):
        self._wrapped_instance.set_array(data["image"])
        self._wrapped_instance.set_extent([*data["xextent"], *data["yextent"]])


class StepWrapper(ProxyWrapper):
    _wrapped_class = _StepPatch
    _privtized_methods = ()  # ("set_data", "get_data")
    required_keys = {"edges", "density"}

    def __init__(self, data: DataContainer, converters=None, /, **kwargs):
        super().__init__(data, converters)
        self._wrapped_instance = self._wrapped_class([], [1], **kwargs)

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(
            self._query_and_transform(renderer),
        )
        return self._wrapped_instance.draw(renderer)

    def _update_wrapped(self, data):
        self._wrapped_instance.set_data(data["density"], data["edges"])


class FormattedText(ProxyWrapper):
    _wrapped_class = _Text
    _privtized_methods = ("set_text",)

    def __init__(self, data: DataContainer, converters=None, /, **kwargs):
        super().__init__(data, converters)
        self._wrapped_instance = self._wrapped_class(text="", **kwargs)

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(
            self._query_and_transform(renderer),
        )
        return self._wrapped_instance.draw(renderer)

    def _update_wrapped(self, data):
        for k, v in data.items():
            getattr(self._wrapped_instance, f"set_{k}")(v)


@_forwarder(
    (
        "set_clip_path",
        "set_clip_box",
        "set_transform",
        "set_snap",
        "set_sketch_params",
        "set_animated",
        "set_picker",
        "set_figure",
    )
)
# _Artist has to go last for now because it is not (yet) MI friendly.
class MultiProxyWrapper(ProxyWrapperBase, _Artist):
    _privtized_methods: Tuple[str, ...] = ()
    _wrapped_instances: Dict[str, _Aritst]

    def __setattr__(self, key, value):
        attrs = set(get_type_hints(type(self)))
        if key in attrs:
            super().__setattr__(key, value)
        if hasattr(self, "_wrapped_instances"):
            # We can end up with out wrapped instance as part of init
            children_have_attrs = [
                hasattr(c, key) for c in self._wrapped_instances.values()
            ]
            if any(children_have_attrs):
                if not all(children_have_attrs):
                    raise Exception("mixed attributes 😱")
                for art in self.get_children():
                    setattr(art, key, value)

        super().__setattr__(key, value)

    def get_children(self):
        return list(self._wrapped_instances.values())


class ErrorbarWrapper(MultiProxyWrapper):
    required_keys = {"x", "y"}
    expected_keys = {
        f"{axis}{dirc}" for axis in ["x", "y"] for dirc in ["upper", "lower"]
    }

    def __init__(self, data: DataContainer, converters=None, /, **kwargs):
        super().__init__(data, converters)
        # TODO all of the kwarg teasing apart that is needed
        color = kwargs.pop("color", "k")
        lw = kwargs.pop("lw", 2)
        assert len(kwargs) == 0

        l0 = _Line2D([], [], color=color, lw=lw)
        ybars = _LineCollection([], colors=color)
        xbars = _LineCollection([], colors=color)
        xcaps_left = _Line2D([], [], color=color, marker="|", linestyle="none")
        xcaps_right = _Line2D([], [], color=color, marker="|", linestyle="none")
        ycaps_up = _Line2D([], [], color=color, marker="_", linestyle="none")
        ycaps_lower = _Line2D([], [], color=color, marker="_", linestyle="none")

        self._wrapped_instances = {
            "l0": l0,
            "ybars": ybars,
            "xbars": xbars,
            "xcaps_left": xcaps_left,
            "xcaps_right": xcaps_right,
            "ycaps_up": ycaps_up,
            "ycaps_lower": ycaps_lower,
        }

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(
            self._query_and_transform(renderer),
        )
        for k, v in self._wrapped_instances.items():
            v.draw(renderer)

    def _update_wrapped(self, data):
        self._wrapped_instances["l0"].set_data(data["x"], data["y"])

        def set_or_hide(check_key, artist, xkey, ykey):
            if check_key in data:
                self._wrapped_instances[artist].set_data(data[xkey], data[ykey])
                self._wrapped_instances[artist].set_visible(True)
            else:
                self._wrapped_instances[artist].set_visible(False)

        set_or_hide("xupper", "xcaps_right", "xupper", "y")
        set_or_hide("xlower", "xcaps_left", "xlower", "y")
        set_or_hide("yupper", "ycaps_up", "x", "yupper")
        set_or_hide("ylower", "ycaps_lower", "x", "ylower")

        if all(k in data for k in ["yupper", "ylower"]):
            verts = np.empty((len(data["x"]), 2, 2))
            verts[:, 0, 0] = data["x"]
            verts[:, 0, 1] = data["ylower"]
            verts[:, 1, 0] = data["x"]
            verts[:, 1, 1] = data["yupper"]
            self._wrapped_instances["ybars"].set_verts(verts)
            self._wrapped_instances["ybars"].set_visible(True)

        else:
            self._wrapped_instances["ybars"].set_visible(False)

        if all(k in data for k in ["xupper", "xlower"]):
            verts = np.empty((len(data["y"]), 2, 2))
            verts[:, 0, 0] = data["xlower"]
            verts[:, 0, 1] = data["y"]
            verts[:, 1, 0] = data["xupper"]
            verts[:, 1, 1] = data["y"]
            self._wrapped_instances["xbars"].set_verts(verts)
            self._wrapped_instances["xbars"].set_visible(True)

        else:
            self._wrapped_instances["xbars"].set_visible(False)

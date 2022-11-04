import numpy as np

from .wrappers import ProxyWrapper, _stale_wrapper
from .containers import DataContainer

from matplotlib.patches import Patch as _Patch, Rectangle as _Rectangle


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
    _xunits = ()
    _yunits = ()
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

    def __init__(self, data: DataContainer, nus=None, /, **kwargs):
        super().__init__(data, nus, xunits=self._xunits, yunits=self._yunits)
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
    _xunits = ("x", "width")
    _yunits = ("y", "height")
    required_keys = PatchWrapper.required_keys | {"x", "y", "width", "height", "angle", "rotation_point"}

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

import numpy as np

from .wrappers import ProxyWrapper, _stale_wrapper
from .containers import DataContainer

from matplotlib.patches import (
    Patch as _Patch,
    Annulus as _Annulus,
    Ellipse as _Ellipse,
    Circle as _Circle,
    Arc as _Arc,
    Rectangle as _Rectangle,
)


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
        super().__init__(data, nus)
        # FIXME this is a bit of an ugly hack, basically we want a null instance
        # because all attributes are determined at draw time, but each class has different signatures
        # The one used here is surprisingly common, but perhaps instantiation should be pushed to the subclasses
        # Additionally, hasattr breaks for recursion depth which should be looked at
        try:
            self._wrapped_instance = self._wrapped_class((0, 0), 0, **kwargs)
        except TypeError:
            self._wrapped_instance = self._wrapped_class((0, 0), 1, 0, **kwargs)

    @_stale_wrapper
    def draw(self, renderer):
        self._update_wrapped(self._query_and_transform(renderer, xunits=self._xunits, yunits=self._yunits))
        return self._wrapped_instance.draw(renderer)

    def _update_wrapped(self, data):
        for k, v in data.items():
            # linestyle and hatch do not work as arrays,
            # but ArrayContainer requires arrays, so index into an array if needed
            if k in ("linestyle", "hatch"):
                if isinstance(v, np.ndarray):
                    v = v[0]
            getattr(self._wrapped_instance, f"set_{k}")(v)


class RectangleWrapper(PatchWrapper):
    _wrapped_class = _Rectangle
    _privtized_methods = PatchWrapper._privtized_methods + (
        "get_x",
        "get_y",
        "get_width",
        "get_height",
        "get_angle",
        "get_rotation_point",
        "set_x",
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
            # rotation_point is a property without a set_rotation_point method
            if k == "rotation_point":
                self._wrapped_instance.rotation_point = v
                continue
            # linestyle and hatch do not work as arrays,
            # but ArrayContainer requires arrays, so index into an array if needed
            elif k in ("linestyle", "hatch"):
                if isinstance(v, np.ndarray):
                    v = v[0]
            getattr(self._wrapped_instance, f"set_{k}")(v)


class AnnulusWrapper(PatchWrapper):
    _wrapped_class = _Annulus
    _privtized_methods = PatchWrapper._privtized_methods + (
        "get_angle",
        "get_center",
        "get_radii",
        "get_width",
        "set_angle",
        "set_center",
        "set_radii",
        "set_width",
        # set_semi[major|minor] overlap with set_radii
    )
    # TODO: units, because "center" is one x and one y units
    # Other things like semi-axis and width seem to _not_ be unit-ed, but maybe _could_ be
    _xunits = ()
    _yunits = ()
    # Order is actually important... radii must come before width
    required_keys = PatchWrapper.required_keys | {"center", "radii", "width", "angle"}


class EllipseWrapper(PatchWrapper):
    _wrapped_class = _Ellipse
    _privtized_methods = PatchWrapper._privtized_methods + (
        "get_angle",
        "get_center",
        "get_width",
        "get_height",
        "set_angle",
        "set_center",
        "set_width",
        "set_height",
    )
    # TODO: units, because "center" is one x and one y units
    _xunits = ("width",)
    _yunits = ("height",)
    required_keys = PatchWrapper.required_keys | {"center", "width", "height", "angle"}


# While the actual patch inherits from ellipse, using it as a full ellipse doesn't make sense
# Therefore, the privitized methods, required keys, etc are not inheritied from EllipseWrapper
class CircleWrapper(PatchWrapper):
    _wrapped_class = _Circle
    _privtized_methods = PatchWrapper._privtized_methods + (
        "get_radius",
        "get_center",
        "set_radius",
        "set_center",
    )
    # TODO: units, because "center" is one x and one y units
    # And "radius" is _both_ x and y units, so may not make sense unless units are the same
    _xunits = ()
    _yunits = ()
    required_keys = PatchWrapper.required_keys | {"center", "radius"}


# Unlike Circle, Arc maintains width/height/etc from Ellipse
class ArcWrapper(EllipseWrapper):
    _wrapped_class = _Arc
    _privtized_methods = EllipseWrapper._privtized_methods + (
        "get_radius",
        "get_center",
        "get_theta1",
        "get_theta2",
        "set_radius",
        "set_center",
        "set_theta1",
        "set_theta2",
    )
    # TODO: units, because "center" is one x and one y units
    # And theta1/2 could arguably pass through a units pipeline, but not the x/y one...
    _xunits = ()
    _yunits = ()
    required_keys = EllipseWrapper.required_keys | {"theta1", "theta2"}

    def _update_wrapped(self, data):
        for k, v in data.items():
            # theta[1,2] are properties without a set_rotation_point method
            if k.startswith("theta"):
                if isinstance(v, np.ndarray):
                    v = v[0]
                setattr(self._wrapped_instance, k, v)
                continue
            # linestyle and hatch do not work as arrays,
            # but ArrayContainer requires arrays, so index into an array if needed
            elif k in ("linestyle", "hatch"):
                if isinstance(v, np.ndarray):
                    v = v[0]
            getattr(self._wrapped_instance, f"set_{k}")(v)

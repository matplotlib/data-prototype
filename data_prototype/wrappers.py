from typing import List, Dict, Any

import numpy as np

from cachetools import LFUCache

from matplotlib.lines import Line2D as _Line2D
from matplotlib.image import AxesImage as _AxesImage


class ProxyWrapper:
    _privtized_methods = ()
    _wrapped_class = None
    _wrapped_instance = None
    data = None

    def draw(self, renderer):
        raise NotImplementedError

    def __getattr__(self, key):
        if key in self._privtized_methods:
            raise AttributeError(f"The method {key} has been privitized")
        if key[0] == "_" and key[1:] in self._privtized_methods:
            return getattr(self._wrapped_instance, key[1:])
        return getattr(self._wrapped_instance, key)

    def __setattr__(self, key, value):
        if hasattr(self._wrapped_instance, key):
            setattr(self._wrapped_instance, key, value)
        else:
            super().__setattr__(key, value)

    def _query_and_transform(self, renderer, *, xunits: List[str], yunits: List[str]) -> Dict[str, Any]:
        """
        Helper to centralize the data querying and python-side transforms

        Parameters
        ----------
        renderer : RendererBase
        xunits, yunits : List[str]
            The list of keys that need to be run through the x and y unit machinery.
        """
        # extract what we need to about the axes to query the data
        ax = self._wrapped_instance.axes
        # TODO do we want to trust the implicit renderer on the Axes?
        ax_bbox = ax.get_window_extent(renderer)

        # actually query the underlying data.  This returns both the (raw) data
        # and key to use for caching.
        data, cache_key = self.data.query(
            # TODO do this need to be (de) unitized
            (*ax.get_xlim(), *ax.get_ylim()),
            tuple(np.round(ax_bbox.size).astype(int)),
            # TODO sort out how to spell the x/y scale
            # TODO is scale enoguh?  What do we have to do about non-trivial projection?
            xscale=None,
            yscale=None,
        )
        # see if we can short-circuit
        try:
            return self._cache[cache_key]
        except KeyError:
            ...
        # TODO decide if units go pre-nu or post-nu?
        for x_like in xunits:
            data[x_like] = ax.xaxis.convert_units(data[x_like])
        for y_like in yunits:
            data[y_like] = ax.xaxis.convert_units(data[y_like])

        # doing the nu work here is nice because we can write it once, but we
        # really want to push this computation down a layer
        # TODO sort out how this interaporates with the transform stack
        data = {k: self.nus.get(k, lambda x: x)(v) for k, v in data.items()}
        self._cache[cache_key] = data
        return data

    def __init__(self, data, nus):
        self.data = data
        self._cache = LFUCache(64)
        # TODO make sure mutating this will invalidate the cache!
        self.nus = nus or {}


class LineWrapper(ProxyWrapper):
    _wrapped_class = _Line2D
    _privtized_methods = set(["set_xdata", "set_ydata", "set_data"])

    def __init__(self, data, nus=None, /, **kwargs):
        super().__init__(data, nus)
        self._wrapped_instance = self._wrapped_class([], [], **kwargs)

    def draw(self, renderer):
        data = self._query_and_transform(renderer, xunits=["x"], yunits=["y"])
        self._wrapped_instance.set_data(data["x"], data["y"])
        return self._wrapped_instance.draw(renderer)


class ImageWrapper(ProxyWrapper):
    _wrapped_class = _AxesImage

    def __init__(self, data, nus=None, /, **kwargs):
        super().__init__(data, nus)
        kwargs.setdefault("origin", "lower")
        self._wrapped_instance = self._wrapped_class(None, **kwargs)

    def draw(self, renderer):
        data = self._query_and_transform(renderer, xunits=["xextent"], yunits=["yextent"])
        self._wrapped_instance.set_array(data["image"])
        self._wrapped_instance.set_extent([*data["xextent"], *data["yextent"]])
        return self._wrapped_instance.draw(renderer)

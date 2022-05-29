import numpy as np


class DataContainer:
    def query(self, data_bounds, size, xscale=None, yscale=None):
        raise NotImplementedError


class ArrayContainer:
    def __init__(self, **data):
        self._data = data

    def query(self, data_bounds, size, xscale=None, yscale=None):
        return dict(self._data)


class FuncContainer:
    def __init__(self, xfuncs, yfuncs=None, xyfuncs=None):
        self._xfuncs = xfuncs or {}
        self._yfuncs = yfuncs or {}
        self._xyfuncs = xyfuncs or {}

    def query(self, data_bounds, size, xscale=None, yscale=None):
        hash_key = hash((data_bounds, size, xscale, yscale))
        if hash_key in self._cache:
            return self._cache[hash_key], hash_key
        xmin, xmax, ymin, ymax = data_bounds
        xpix, ypix = size
        x_data = np.linspace(xmin, xmax, int(xpix) * 2)
        y_data = np.linspace(ymin, ymax, int(ypix) * 2)
        ret = self._cache[hash_key] = dict(
            **{k: f(x_data) for k, f in self._xfuncs.items()},
            **{k: f(y_data) for k, f in self._yfuncs.items()},
            **{k: f(x_data, y_data) for k, f in self._xyfuncs.items()}
        )
        return ret, hash_key

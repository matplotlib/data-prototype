from dataclasses import dataclass
from typing import Protocol, List, Dict, Tuple, Optional, Any, Union, Callable, MutableMapping
import uuid

import numpy as np

from cachetools import LFUCache


@dataclass(frozen=True)
class Desc:
    # TODO: sort out how to actually spell this.  We need to know:
    #   - what the number of dimensions is (1d vs 2d vs ...)
    #   - is this a fixed size dimension (e.g. 2 for xextent)
    #   - is this a variable size depending on the query (e.g. N)
    #   - what is the relative size to the other variable values (N vs N+1)
    # We are probably going to have to implement a DSL for this (😞)
    shape: List[Union[str, int]]
    # TODO: is using a string better?
    dtype_str: np.dtype
    # TODO: do we want to include this at this level?  "naive" means unit-unaware.
    units: str = "naive"


class DataContainer(Protocol):
    def query(
        self,
        # TODO 3D?!!
        data_bounds: Tuple[float, float, float, float],
        size: Tuple[int, int],
        xscale: Optional[str] = None,
        yscale: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        """
        Query the data container for data.

        We are given the data limits and the screen size so that we have an
        estimate of how finely (or not) we need to sample the data we wrapping.

        Parameters
        ----------
        data_bounds : 4 floats
            xmin, xmax, ymin, ymax

            The bounds in data-coordinates of interest.

        size : 2 integers
            xpixels, ypixels

            The size in screen / render units that we have to fill.

        xscale, yscale : str or None
            If the underlying scale is non-linear we may not want to sample
            the data linearly.  For example if the scale is log, we probably
            want to sample the data evenly in log space.

        Returns
        -------
        data : Dict[str, Any]
            The values are really array-likes, but 🤷 how to spell that in typing given
            that the dimension and type will depend on the key / how it is set up and the
            size may depend on the input values

        cache_key : str
            This is a key that clients can use to cache down-stream
            computations on this data.
        """

    def describe(self) -> Dict[str, Desc]:
        """
        Describe the data a query will return

        Returns
        -------
        Dict[str, Desc]
        """


class ArrayContainer:
    def __init__(self, **data):
        self._data = data
        self._cache_key = str(uuid.uuid4())
        self._desc = {k: Desc(v.shape, v.dype) for k, v in data}

    def query(
        self,
        data_bounds: Tuple[float, float, float, float],
        size: Tuple[int, int],
        xscale: Optional[str] = None,
        yscale: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        return dict(self._data), self._cache_key

    def describe(self):
        return dict(self._desc)


class RandomContainer:
    def __init__(self, **shapes):
        self._desc = {k: Desc(s, np.dtype(float)) for k, s in shapes.items()}

    def query(
        self,
        data_bounds: Tuple[float, float, float, float],
        size: Tuple[int, int],
        xscale: Optional[str] = None,
        yscale: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        return {k: np.random.randn(d.shape) for k, d in self._desc.items()}, str(uuid.uuid4())

    def describe(self):
        return dict(self._desc)


class FuncContainer:
    def __init__(
        self,
        # TODO: is this really the best spelling?!
        xfuncs: Optional[Dict[str, Tuple[List[Union[str, int]], Callable[[Any], Any]]]] = None,
        yfuncs: Optional[Dict[str, Tuple[List[Union[str, int]], Callable[[Any], Any]]]] = None,
        xyfuncs: Optional[Dict[str, Tuple[List[Union[str, int]], Callable[[Any, Any], Any]]]] = None,
    ):
        """
        A container that wraps several functions.  They are split into 3 categories:

          - functions that are offered x-like values as input
          - functions that are offered y-like values as input
          - functions that are offered both x and y like values as two inputs

        In addition to the callable, the user needs to provide a spelling of
        what the (relative) shapes will be in relation to each other. For now this
        is a list of integers and strings, where the strings are "generic" values.

        For example if two functions report shapes: ``{'bins':[N],  'edges': [N + 1]`` then
        when called, *edges* will always have one more entry than bins.

        Parameters
        ----------
        xfuncs, yfuncs, xyfuncs : Dict[str, Tuple[shape, func]]

        """
        # TODO validate no collisions
        self._desc: Dict[str, Desc] = {}

        def _split(input_dict):
            out = {}
            for k, (shape, func) in input_dict.items():
                self._desc[k] = Desc(shape, np.dtype(float))
                out[k] = func
            return out

        self._xfuncs = _split(xfuncs) if xfuncs is not None else {}
        self._yfuncs = _split(yfuncs) if yfuncs is not None else {}
        self._xyfuncs = _split(xyfuncs) if xyfuncs is not None else {}
        self._cache: MutableMapping[Union[str, int], Any] = LFUCache(64)

    # cache could go here!
    def query(
        self,
        data_bounds: Tuple[float, float, float, float],
        size: Tuple[int, int],
        xscale: Optional[str] = None,
        yscale: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
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

    def describe(self):
        return dict(self._desc)


class WebServiceContainer:
    def query(
        self,
        data_bounds: Tuple[float, float, float, float],
        size: Tuple[int, int],
        xscale: Optional[str] = None,
        yscale: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        def hit_some_database():
            {}, "1"

        data, etag = hit_some_database()
        return data, etag

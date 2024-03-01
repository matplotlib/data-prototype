from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Protocol,
    Dict,
    Tuple,
    Optional,
    Any,
    Union,
    Callable,
    MutableMapping,
    TypeAlias,
)
import uuid

from cachetools import LFUCache

import numpy as np
import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conversion_edge import Graph


class _MatplotlibTransform(Protocol):
    def transform(self, verts):
        ...

    def __sub__(self, other) -> "_MatplotlibTransform":
        ...


ShapeSpec: TypeAlias = Tuple[Union[str, int], ...]


@dataclass(frozen=True)
class Desc:
    # TODO: sort out how to actually spell this.  We need to know:
    #   - what the number of dimensions is (1d vs 2d vs ...)
    #   - is this a fixed size dimension (e.g. 2 for xextent)
    #   - is this a variable size depending on the query (e.g. N)
    #   - what is the relative size to the other variable values (N vs N+1)
    # We are probably going to have to implement a DSL for this (😞)
    shape: ShapeSpec
    dtype: np.dtype
    coordinates: str = "naive"

    @staticmethod
    def validate_shapes(
        specification: dict[str, ShapeSpec | "Desc"],
        actual: dict[str, ShapeSpec | "Desc"],
        *,
        broadcast: bool = False,
    ) -> None:
        """Validate specified shape relationships against a provided set of shapes.

        Shapes provided are tuples of int | str. If a specification calls for an int,
        the exact size is expected.
        If it is a str, it must be a single capital letter optionally followed by ``+``
        or ``-`` an integer value.
        The same letter used in the specification must represent the same value in all
        appearances. The value may, however, be a variable (with an offset) in the
        actual shapes (which does not need to have the same letter).

        Shapes may be provided as raw tuples or as ``Desc`` objects.

        Parameters
        ----------
        specification: dict[str, ShapeSpec | "Desc"]
           The desired shape relationships
        actual: dict[str, ShapeSpec | "Desc"]
           The shapes to test for compliance

        Keyword Parameters
        ------------------
        broadcast: bool
           Whether to allow broadcasted shapes to pass (i.e. actual shapes with a ``1``
           will not cause exceptions regardless of what the specified shape value is)

        Raises
        ------
        KeyError:
            If a required field from the specification is missing in the provided actual
            values.
        ValueError:
            If shapes are incompatible in any other way
        """
        specvars: dict[str, int | tuple[str, int]] = {}
        for fieldname in specification:
            spec = specification[fieldname]
            if fieldname not in actual:
                raise KeyError(
                    f"Actual is missing {fieldname!r}, required by specification."
                )
            desc = actual[fieldname]
            if isinstance(spec, Desc):
                spec = spec.shape
            if isinstance(desc, Desc):
                desc = desc.shape
            if not broadcast:
                if len(spec) != len(desc):
                    raise ValueError(
                        f"{fieldname!r} shape {desc} incompatible with specification "
                        f"{spec}."
                    )
            elif len(desc) > len(spec):
                raise ValueError(
                    f"{fieldname!r} shape {desc} incompatible with specification "
                    f"{spec}."
                )
            for speccomp, desccomp in zip(spec[::-1], desc[::-1]):
                if broadcast and desccomp == 1:
                    continue
                if isinstance(speccomp, str):
                    specv, specoff = speccomp[0], int(speccomp[1:] or 0)

                    if isinstance(desccomp, str):
                        descv, descoff = desccomp[0], int(desccomp[1:] or 0)
                        entry = (descv, descoff - specoff)
                    else:
                        entry = desccomp - specoff

                    if specv in specvars and entry != specvars[specv]:
                        raise ValueError(f"Found two incompatible values for {specv!r}")

                    specvars[specv] = entry
                elif speccomp != desccomp:
                    raise ValueError(
                        f"{fieldname!r} shape {desc} incompatible with specification "
                        f"{spec}"
                    )
        return None

    @staticmethod
    def compatible(a: dict[str, Desc], b: dict[str, Desc]) -> bool:
        """Determine if ``a`` is a valid input for ``b``.

        Note: ``a`` _may_ have additional keys.
        """
        try:
            Desc.validate_shapes(b, a)
        except (KeyError, ValueError):
            return False
        for k, v in b.items():
            if a[k].coordinates != v.coordinates:
                return False
        return True


class DataContainer(Protocol):
    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
        /,
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        """
        Query the data container for data.

        We are given the data limits and the screen size so that we have an
        estimate of how finely (or not) we need to sample the data we wrapping.

        Parameters
        ----------
        coord_transform : matplotlib.transform.Transform
            Must go from axes fraction space -> data space

        size : 2 integers
            xpixels, ypixels

            The size in screen / render units that we have to fill.

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


class NoNewKeys(ValueError):
    ...


class ArrayContainer:
    def __init__(self, **data):
        self._data = data
        self._cache_key = str(uuid.uuid4())
        self._desc = {
            k: Desc(v.shape, v.dtype)
            if isinstance(v, np.ndarray)
            else Desc((), type(v))
            for k, v in data.items()
        }

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        return dict(self._data), self._cache_key

    def describe(self) -> Dict[str, Desc]:
        return dict(self._desc)

    def update(self, **data):
        # TODO check that this is still consistent with desc!
        if not all(k in self._data for k in data):
            raise NoNewKeys(
                f"The keys that currently exist are {set(self._data)}.  You "
                f"tried to add {set(data) - set(self._data)!r}."
            )
        self._data.update(data)
        self._cache_key = str(uuid.uuid4())


class RandomContainer:
    def __init__(self, **shapes):
        self._desc = {k: Desc(s, np.dtype(float)) for k, s in shapes.items()}

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        return {k: np.random.randn(*d.shape) for k, d in self._desc.items()}, str(
            uuid.uuid4()
        )

    def describe(self) -> Dict[str, Desc]:
        return dict(self._desc)


class FuncContainer:
    def __init__(
        self,
        # TODO: is this really the best spelling?!
        xfuncs: Optional[
            Dict[str, Tuple[Tuple[Union[str, int], ...], Callable[[Any], Any]]]
        ] = None,
        yfuncs: Optional[
            Dict[str, Tuple[Tuple[Union[str, int], ...], Callable[[Any], Any]]]
        ] = None,
        xyfuncs: Optional[
            Dict[str, Tuple[Tuple[Union[str, int], ...], Callable[[Any, Any], Any]]]
        ] = None,
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

    def _query_hash(self, coord_transform, size):
        # TODO find a better way to compute the hash key, this is not sentative to
        # scale changes, only limit changes
        data_bounds = tuple(coord_transform.transform([[0, 0], [1, 1]]).flatten())
        hash_key = hash((data_bounds, size))
        return hash_key

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        # hash_key = self._query_hash(coord_transform, size)
        # if hash_key in self._cache:
        #    return self._cache[hash_key], hash_key

        data_lim = graph.evaluator(
            {
                "x": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates="data",
                ),
                "y": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates="data",
                ),
            },
            {
                "x": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates=parent_coordinates,
                ),
                "y": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates=parent_coordinates,
                ),
            },
        ).inverse
        screen_size = graph.evaluator(
            {
                "x": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates=parent_coordinates,
                ),
                "y": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates=parent_coordinates,
                ),
            },
            {
                "x": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates="display",
                ),
                "y": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates="display",
                ),
            },
        )

        screen_dims = screen_size.evaluate({"x": [0, 1], "y": [0, 1]})
        xpix, ypix = np.ceil(np.abs(np.diff(screen_dims["x"]))), np.ceil(
            np.abs(np.diff(screen_dims["y"]))
        )

        x_data = data_lim.evaluate(
            {
                "x": np.linspace(0, 1, int(xpix) * 2),
                "y": np.zeros(int(xpix) * 2),
            }
        )["x"]
        y_data = data_lim.evaluate(
            {
                "x": np.zeros(int(ypix) * 2),
                "y": np.linspace(0, 1, int(ypix) * 2),
            }
        )["y"]

        hash_key = str(uuid.uuid4())
        ret = self._cache[hash_key] = dict(
            **{k: f(x_data) for k, f in self._xfuncs.items()},
            **{k: f(y_data) for k, f in self._yfuncs.items()},
            **{k: f(x_data, y_data) for k, f in self._xyfuncs.items()},
        )
        return ret, hash_key

    def describe(self) -> Dict[str, Desc]:
        return dict(self._desc)


class HistContainer:
    def __init__(self, raw_data, num_bins: int):
        self._raw_data = raw_data
        self._num_bins = num_bins
        self._desc = {
            "edges": Desc((num_bins + 1 + 2,), np.dtype(float)),
            "density": Desc((num_bins + 2,), np.dtype(float)),
        }
        self._full_range = (raw_data.min(), raw_data.max())
        self._cache: MutableMapping[Union[str, int], Any] = LFUCache(64)

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        dmin, dmax = self._full_range

        data_lim = graph.evaluator(
            {
                "x": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates="data",
                ),
                "y": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates="data",
                ),
            },
            {
                "x": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates=parent_coordinates,
                ),
                "y": Desc(
                    ("N",),
                    np.dtype(
                        "f8",
                    ),
                    coordinates=parent_coordinates,
                ),
            },
        ).inverse

        pts = data_lim.evaluate({"x": (0, 1), "y": (0, 1)})
        xmin, xmax = pts["x"]
        ymin, ymax = pts["y"]

        xmin, xmax = np.clip([xmin, xmax], dmin, dmax)
        hash_key = hash((xmin, xmax))
        if hash_key in self._cache:
            return self._cache[hash_key], hash_key
        # TODO this gives an artifact with high lw
        edges_in = []
        if dmin < xmin:
            edges_in.append(np.array([dmin]))
        edges_in.append(np.linspace(xmin, xmax, self._num_bins))
        if xmax < dmax:
            edges_in.append(np.array([dmax]))

        density, edges = np.histogram(
            self._raw_data,
            bins=np.concatenate(edges_in),
            density=True,
        )
        ret = self._cache[hash_key] = {"edges": edges, "density": density}
        return ret, hash_key

    def describe(self) -> Dict[str, Desc]:
        return dict(self._desc)


class SeriesContainer:
    _data: pd.DataFrame
    _index_name: str
    _hash_key: str

    def __init__(self, series: pd.Series, *, index_name: str, col_name: str):
        # TODO make a copy?
        self._data = series
        self._index_name = index_name
        self._col_name = col_name
        self._desc = {
            index_name: Desc((len(series),), series.index.dtype),
            col_name: Desc((len(series),), series.dtype),
        }
        self._hash_key = str(uuid.uuid4())

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        return {
            self._index_name: self._data.index.values,
            self._col_name: self._data.values,
        }, self._hash_key

    def describe(self) -> Dict[str, Desc]:
        return dict(self._desc)


class DataFrameContainer:
    _data: pd.DataFrame

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        col_names: Union[Callable[[str], str], Dict[str, str]],
        index_name: Optional[str] = None,
    ):
        # TODO make a copy?
        self._data = df
        self._index_name = index_name

        if callable(col_names):
            # TODO cache the function so we can replace the dataframe later?
            self._col_name_dict = {k: col_names(k) for k in df.columns}
        else:
            self._col_name_dict = dict(col_names)

        self._desc: Dict[str, Desc] = {}
        if self._index_name is not None:
            self._desc[self._index_name] = Desc((len(df),), df.index.dtype)
        for col, out in self._col_name_dict.items():
            self._desc[out] = Desc((len(df),), df[col].dtype)

        self._hash_key = str(uuid.uuid4())

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        ret = {}
        if self._index_name is not None:
            ret[self._index_name] = self._data.index.values
        for col, out in self._col_name_dict.items():
            ret[out] = self._data[col].values

        return ret, self._hash_key

    def describe(self) -> Dict[str, Desc]:
        return dict(self._desc)


class ReNamer:
    def __init__(self, data: DataContainer, mapping: Dict[str, str]):
        # TODO: check all the asked for key exist
        self._data = data
        self._mapping = mapping

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        base, cache_key = self._data.query(graph, parent_coordinates)
        return {v: base[k] for k, v in self._mapping.items()}, cache_key

    def describe(self):
        base = self._data.describe()
        return {v: base[k] for k, v in self._mapping.items()}


class DataUnion:
    def __init__(self, *data: DataContainer):
        # TODO check no collisions
        self._datas = data

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        cache_keys = []
        ret = {}
        for data in self._datas:
            base, cache_key = data.query(graph, parent_coordinates)
            ret.update(base)
            cache_keys.append(cache_key)
        return ret, hash(tuple(cache_keys))

    def describe(self):
        return {k: v for d in self._datas for k, v in d.describe().items()}


class WebServiceContainer:
    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        def hit_some_database():
            {}, "1"

        data, etag = hit_some_database()
        return data, etag

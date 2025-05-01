"""
===========================================
Using pint units with PathCollectionWrapper
===========================================

Using third party units functionality in conjunction with Matplotlib Axes
"""

import numpy as np
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.markers as mmarkers

from mpl_data_containers.artist import CompatibilityAxes
from mpl_data_containers.containers import ArrayContainer
from mpl_data_containers.conversion_edge import FuncEdge
from mpl_data_containers.description import Desc

from mpl_data_containers.line import Line

import pint

ureg = pint.UnitRegistry()
ureg.setup_matplotlib()

marker_obj = mmarkers.MarkerStyle("o")


coords = defaultdict(lambda: "auto")
coords["x"] = coords["y"] = "units"
cont = ArrayContainer(
    coords,
    x=np.array([0, 1, 2]) * ureg.m,
    y=np.array([1, 4, 2]) * ureg.m,
    paths=np.array([marker_obj.get_path()]),
    sizes=np.array([12]),
    edgecolors=np.array(["k"]),
    facecolors=np.array(["C3"]),
)

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
ax.set_xlim(-0.5, 7)
ax.set_ylim(0, 5)

scalar = Desc((), "units")
unit_vector = Desc(("N",), "units")

xconv = FuncEdge.from_func(
    "xconv",
    lambda x, xunits: x.to(xunits).magnitude,
    {"x": unit_vector, "xunits": scalar},
    {"x": Desc(("N",), "data")},
)
yconv = FuncEdge.from_func(
    "yconv",
    lambda y, yunits: y.to(yunits).magnitude,
    {"y": unit_vector, "yunits": scalar},
    {"y": Desc(("N",), "data")},
)
lw = Line(cont, [xconv, yconv])

ax.add_artist(lw)
nax.xaxis.set_units(ureg.ft)
nax.yaxis.set_units(ureg.m)

plt.show()

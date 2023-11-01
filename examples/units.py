"""
==================================================
An simple scatter plot using PathCollectionWrapper
==================================================

A quick scatter plot using :class:`.containers.ArrayContainer` and
:class:`.wrappers.PathCollectionWrapper`.
"""
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.markers as mmarkers

from data_prototype.containers import ArrayContainer
from data_prototype.conversion_node import MatplotlibUnitConversion

from data_prototype.wrappers import PathCollectionWrapper

import pint

ureg = pint.UnitRegistry()
ureg.setup_matplotlib()

marker_obj = mmarkers.MarkerStyle("o")

cont = ArrayContainer(
    x=np.array([0, 1, 2]) * ureg.m,
    y=np.array([1, 4, 2]) * ureg.m,
    paths=np.array([marker_obj.get_path()]),
    sizes=np.array([12]),
    edgecolors=np.array(["k"]),
    facecolors=np.array(["C3"]),
)

fig, ax = plt.subplots()
ax.set_xlim(-0.5, 7)
ax.set_ylim(0, 5)
conv = MatplotlibUnitConversion.from_keys(("x",), axis=ax.xaxis)
lw = PathCollectionWrapper(cont, [conv], offset_transform=ax.transData)
ax.add_artist(lw)
ax.xaxis.set_units(ureg.feet)
plt.show()

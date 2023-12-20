"""
===========================================
Using pint units with PathCollectionWrapper
===========================================

Using third party units functionality in conjunction with Matplotlib Axes
"""
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.markers as mmarkers

from data_prototype.containers import ArrayContainer
from data_prototype.conversion_node import DelayedConversionNode

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

# DelayedConversionNode is used to identify the keys which undergo unit transformations
# The actual method which does conversions in this example is added by the
# `Axis`/`Axes`, but `PathCollectionWrapper` does not natively interact with the units.
xconv = DelayedConversionNode.from_keys(("x",), converter_key="xunits")
yconv = DelayedConversionNode.from_keys(("y",), converter_key="yunits")
lw = PathCollectionWrapper(cont, [xconv, yconv], offset_transform=ax.transData)
ax.add_artist(lw)
ax.xaxis.set_units(ureg.feet)
ax.yaxis.set_units(ureg.m)
plt.show()

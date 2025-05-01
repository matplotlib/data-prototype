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

from mpl_data_containers.containers import ArrayContainer

from mpl_data_containers.wrappers import PathCollectionWrapper

marker_obj = mmarkers.MarkerStyle("o")

cont = ArrayContainer(
    x=np.array([0, 1, 2]),
    y=np.array([1, 4, 2]),
    paths=np.array([marker_obj.get_path()]),
    sizes=np.array([12]),
    edgecolors=np.array(["k"]),
    facecolors=np.array(["C3"]),
)

fig, ax = plt.subplots()
ax.set_xlim(-0.5, 2.5)
ax.set_ylim(0, 5)
lw = PathCollectionWrapper(cont, offset_transform=ax.transData)
ax.add_artist(lw)
plt.show()

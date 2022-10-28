"""
==========================
An animated lissajous ball
==========================

Inspired by https://twitter.com/_brohrer_/status/1584681864648065027


"""
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.markers as mmarkers

from data_prototype.containers import ArrayContainer

from data_prototype.wrappers import PathCollectionWrapper


def update(frame, art):
    return art

marker_obj = mmarkers.MarkerStyle("o")

cont = ArrayContainer(
    x = np.array([0,1,2]),
    y = np.array([1,4,2]),
    paths = np.array([marker_obj.get_path()]),
    sizes = np.array([12]),
    edgecolors = np.array(["k"]),
    facecolors = np.array(["C3"]),
)

fig, ax = plt.subplots()
ax.set_xlim(-.5, 2.5)
ax.set_ylim(0, 5)
lw = PathCollectionWrapper(cont, offset_transform=ax.transData)
ax.add_artist(lw)
#ax.set_xticks([])
#ax.set_yticks([])
#ax.set_aspect(1)
plt.show()

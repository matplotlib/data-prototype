"""
====================
Simple patch artists
====================

Draw two fully specified rectangle patches.
Demonstrates :class:`.patches.RectangleWrapper` using
:class:`.containers.ArrayContainer`.

"""

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from mpl_data_containers.containers import ArrayContainer
from mpl_data_containers.artist import CompatibilityAxes

from mpl_data_containers.patches import Rectangle

cont1 = ArrayContainer(
    lower_left_x=np.array(-3),
    lower_left_y=np.array(0),
    upper_right_x=np.array(-1),
    upper_right_y=np.array(3),
    edgecolor=np.array([0, 0, 0]),
    facecolor="green",
    linewidth=3,
    linestyle="-",
    antialiased=np.array([True]),
    fill=np.array([True]),
    capstyle=np.array(["round"]),
    joinstyle=np.array(["miter"]),
    alpha=np.array(0.5),
)

cont2 = ArrayContainer(
    lower_left_x=0,
    lower_left_y=np.array(1),
    upper_right_x=np.array(2),
    upper_right_y=np.array(5),
    angle=30,
    rotation_point_x=np.array(1),
    rotation_point_y=np.array(3.5),
    edgecolor=np.array([0.5, 0.2, 0]),
    facecolor="red",
    linewidth=6,
    linestyle="-",
    antialiased=np.array([True]),
    fill=np.array([True]),
    capstyle=np.array(["round"]),
    joinstyle=np.array(["miter"]),
)

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
nax.set_xlim(-5, 5)
nax.set_ylim(0, 5)

rect = mpatches.Rectangle((4, 1), 2, 3, linewidth=6, edgecolor="black", angle=30)
nax.add_artist(rect)

rect1 = Rectangle(cont1, {})
rect2 = Rectangle(cont2, {})
ax.add_artist(rect1)
ax.add_artist(rect2)
nax.set_aspect(1)
plt.show()

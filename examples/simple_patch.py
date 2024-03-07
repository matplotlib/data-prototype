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

from data_prototype.containers import ArrayContainer

from data_prototype.patches import RectangleWrapper

cont1 = ArrayContainer(
    x=np.array([-3]),
    y=np.array([0]),
    width=np.array([2]),
    height=np.array([3]),
    angle=np.array([0]),
    rotation_point=np.array(["center"]),
    edgecolor=np.array([0, 0, 0]),
    facecolor=np.array([0.0, 0.7, 0, 0.5]),
    linewidth=np.array([3]),
    linestyle=np.array(["-"]),
    antialiased=np.array([True]),
    hatch=np.array(["*"]),
    fill=np.array([True]),
    capstyle=np.array(["round"]),
    joinstyle=np.array(["miter"]),
)

cont2 = ArrayContainer(
    x=np.array([0]),
    y=np.array([1]),
    width=np.array([2]),
    height=np.array([3]),
    angle=np.array([30]),
    rotation_point=np.array(["center"]),
    edgecolor=np.array([0, 0, 0]),
    facecolor=np.array([0.7, 0, 0]),
    linewidth=np.array([6]),
    linestyle=np.array(["-"]),
    antialiased=np.array([True]),
    hatch=np.array([""]),
    fill=np.array([True]),
    capstyle=np.array(["butt"]),
    joinstyle=np.array(["round"]),
)

fig, ax = plt.subplots()
ax.set_xlim(-5, 5)
ax.set_ylim(0, 5)
rect1 = RectangleWrapper(cont1, {})
rect2 = RectangleWrapper(cont2, {})
ax.add_artist(rect1)
ax.add_artist(rect2)
ax.set_aspect(1)
plt.show()

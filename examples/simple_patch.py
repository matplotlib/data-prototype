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

from data_prototype.patches import RectangleWrapper, CircleWrapper, AnnulusWrapper, EllipseWrapper

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
    center=np.array([0, 1]),
    radius=np.array([0.8]),
    edgecolor=np.array([0, 0, 0]),
    facecolor=np.array([0.7, 0, 0]),
    linewidth=np.array([3]),
    linestyle=np.array(["-"]),
    antialiased=np.array([True]),
    hatch=np.array([""]),
    fill=np.array([True]),
    capstyle=np.array(["butt"]),
    joinstyle=np.array(["round"]),
)

cont3 = ArrayContainer(
    center=np.array([0, 4]),
    width=np.array([2]),
    height=np.array([1]),
    angle=np.array([0.3]),
    edgecolor=np.array([0, 0, 0.7]),
    facecolor=np.array([0, 0.7, 0]),
    linewidth=np.array([3]),
    linestyle=np.array([":"]),
    antialiased=np.array([True]),
    hatch=np.array(["/"]),
    fill=np.array([True]),
    capstyle=np.array(["butt"]),
    joinstyle=np.array(["round"]),
)

cont4 = ArrayContainer(
    center=np.array([1, 4]),
    radii=np.array([3, 1]),
    width=np.array([0.4]),
    height=np.array([1]),
    angle=np.array([0.3]),
    theta1=np.array([0]),
    theta2=np.array([2]),
    edgecolor=np.array([0, 0.7, 0]),
    facecolor=np.array([0.7, 0, 0.7]),
    linewidth=np.array([3]),
    linestyle=np.array(["-"]),
    antialiased=np.array([True]),
    hatch=np.array(["+"]),
    fill=np.array([True]),
    capstyle=np.array(["butt"]),
    joinstyle=np.array(["round"]),
)

fig, ax = plt.subplots()
ax.set_xlim(-5, 5)
ax.set_ylim(0, 5)
rect = RectangleWrapper(cont1, {})
circ = CircleWrapper(cont2, {})
ellipse = EllipseWrapper(cont3, {})

# ArcWrapper is still broken due to no setters of theta1/2
# arc = ArcWrapper(cont4, {})

annulus = AnnulusWrapper(cont4, {})
ax.add_artist(rect)
ax.add_artist(circ)
ax.add_artist(ellipse)
# ax.add_artist(arc)
ax.add_artist(annulus)
ax.set_aspect(1)
plt.show()

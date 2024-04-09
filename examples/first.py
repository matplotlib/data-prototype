"""
=================
A functional line
=================

Demonstrating the differences between :class:`.containers.FuncContainer` and
:class:`.containers.SeriesContainer` using :class:`.artist.Line`.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data_prototype.artist import CompatibilityArtist
from data_prototype.line import Line
from data_prototype.containers import FuncContainer, SeriesContainer

fc = FuncContainer({"x": (("N",), lambda x: x), "y": (("N",), np.sin)})
lw = Line(fc, linewidth=5, color="green", label="sin (function)")

th = np.linspace(0, 2 * np.pi, 16)
sc = SeriesContainer(pd.Series(index=th, data=np.cos(th)), index_name="x", col_name="y")
lw2 = Line(
    sc,
    linewidth=3,
    linestyle=":",
    color="C0",
    label="cos (pandas)",
    marker=".",
    markersize=12,
)

fig, ax = plt.subplots()
ax.add_artist(CompatibilityArtist(lw))
ax.add_artist(CompatibilityArtist(lw2))
ax.set_xlim(0, np.pi * 4)
ax.set_ylim(-1.1, 1.1)

plt.show()

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

from mpl_data_containers.artist import CompatibilityAxes
from mpl_data_containers.line import Line
from mpl_data_containers.containers import FuncContainer, SeriesContainer


fc = FuncContainer({"x": (("N",), lambda x: x), "y": (("N",), lambda x: np.sin(1 / x))})
lw = Line(fc, linewidth=5, color="green", label="sin(1/x) (function)")

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

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
ax.add_artist(lw, 3)
ax.add_artist(lw2, 2)
ax.set_xlim(0, np.pi * 4)
ax.set_ylim(-1.1, 1.1)

plt.show()

"""
===============
Show data frame
===============

Wrapping a :class:`pandas.DataFrame` using :class:`.containers.DataFrameContainer`
and :class:`.artist.Line`.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mpl_data_containers.artist import CompatibilityArtist as CA
from mpl_data_containers.line import Line
from mpl_data_containers.containers import DataFrameContainer

th = np.linspace(0, 4 * np.pi, 256)

dc1 = DataFrameContainer(
    pd.DataFrame({"x": th, "y": np.cos(th)}), index_name=None, col_names=lambda n: n
)

df = pd.DataFrame(
    {
        "cos": np.cos(th),
        "sin": np.sin(th),
    },
    index=th,
)


dc2 = DataFrameContainer(df, index_name="x", col_names={"sin": "y"})
dc3 = DataFrameContainer(df, index_name="x", col_names={"cos": "y"})


fig, (ax1, ax2) = plt.subplots(2, 1)
ax1.add_artist(CA(Line(dc1, linewidth=5, color="green", label="sin")))
ax2.add_artist(CA(Line(dc2, linewidth=5, color="green", label="sin")))
ax2.add_artist(CA(Line(dc3, linewidth=5, color="blue", label="cos")))
for ax in (ax1, ax2):
    ax.set_xlim(0, np.pi * 4)
    ax.set_ylim(-1.1, 1.1)

plt.show()

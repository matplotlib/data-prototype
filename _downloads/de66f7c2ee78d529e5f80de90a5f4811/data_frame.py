"""
===============
Show data frame
===============

Wrapping a :class:`pandas.DataFrame` using :class:`.containers.DataFrameContainer`
and :class:`.wrappers.LineWrapper`.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data_prototype.wrappers import LineWrapper
from data_prototype.containers import DataFrameContainer

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
ax1.add_artist(LineWrapper(dc1, lw=5, color="green", label="sin"))
ax2.add_artist(LineWrapper(dc2, lw=5, color="green", label="sin"))
ax2.add_artist(LineWrapper(dc3, lw=5, color="blue", label="cos"))
for ax in (ax1, ax2):
    ax.set_xlim(0, np.pi * 4)
    ax.set_ylim(-1.1, 1.1)

plt.show()

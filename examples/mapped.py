"""
=======================
Mapping Line Properties
=======================

Leveraging the nu functions to transform users space data to visualization data.

"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib.colors import Normalize

from data_prototype.wrappers import LineWrapper
from data_prototype.containers import ArrayContainer

cmap = plt.colormaps["viridis"]
cmap.set_over("k")
cmap.set_under("r")
norm = Normalize(1, 8)

nus = {
    # arbitrary functions
    "lw": lambda lw: min(1 + lw, 5),
    # standard color mapping
    "color": lambda color: cmap(norm(color)),
    # categorical
    "ls": lambda ls: {"A": "-", "B": ":", "C": "--"}[ls[()]],
}

th = np.linspace(0, 2 * np.pi, 128)
delta = np.pi / 9

fig, ax = plt.subplots()

for j in range(10):
    ax.add_artist(
        LineWrapper(
            ArrayContainer(
                **{
                    "x": th,
                    "y": np.sin(th + j * delta) + j,
                    "color": np.asarray(j),
                    "lw": np.asarray(j),
                    "ls": np.asarray({0: "A", 1: "B", 2: "C"}[j % 3]),
                }
            ),
            nus,
        )
    )

ax.set_xlim(0, np.pi * 2)
ax.set_ylim(-1.1, 10.1)

plt.show()

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

from data_prototype.wrappers import LineWrapper, FormatedText
from data_prototype.containers import ArrayContainer

cmap = plt.colormaps["viridis"]
cmap.set_over("k")
cmap.set_under("r")
norm = Normalize(1, 8)

nus = {
    # arbitrary functions
    "lw": lambda lw: min(1 + lw, 5),
    # standard color mapping
    "color": lambda j: cmap(norm(j)),
    # categorical
    "ls": lambda cat: {"A": "-", "B": ":", "C": "--"}[cat[()]],
}

th = np.linspace(0, 2 * np.pi, 128)
delta = np.pi / 9

fig, ax = plt.subplots()

for j in range(10):
    ac = ArrayContainer(
        **{
            "x": th,
            "y": np.sin(th + j * delta) + j,
            "j": np.asarray(j),
            "lw": np.asarray(j),
            "cat": np.asarray({0: "A", 1: "B", 2: "C"}[j % 3]),
        }
    )
    ax.add_artist(
        LineWrapper(
            ac,
            nus,
        )
    )
    ax.add_artist(
        FormatedText(
            ac,
            {"text": lambda j, cat: f"index={j[()]} class={cat[()]!r}", "y": lambda j: j},
            x=2 * np.pi,
            ha="right",
            bbox={"facecolor": "gray", "alpha": 0.5},
        )
    )
ax.set_xlim(0, np.pi * 2)
ax.set_ylim(-1.1, 10.1)

plt.show()

"""
=======================
Mapping Line Properties
=======================

Leveraging the converter functions to transform users space data to visualization data.

"""

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.colors import Normalize
from matplotlib.font_manager import FontProperties

from data_prototype.artist import CompatibilityAxes
from data_prototype.line import Line
from data_prototype.containers import ArrayContainer
from data_prototype.description import Desc
from data_prototype.conversion_edge import FuncEdge
from data_prototype.text import Text


cmap = plt.colormaps["viridis"]
cmap.set_over("k")
cmap.set_under("r")
norm = Normalize(1, 8)

line_edges = [
    FuncEdge.from_func(
        "lw",
        lambda lw: min(1 + lw, 5),
        {"lw": Desc((), "auto")},
        {"linewidth": Desc((), "display")},
    ),
    # Probably should separate out norm/cmap step
    # Slight lie about color being a string here, because of limitations in impl
    FuncEdge.from_func(
        "cmap",
        lambda j: cmap(norm(j)),
        {"j": Desc((), "auto")},
        {"color": Desc((), "display")},
    ),
    FuncEdge.from_func(
        "ls",
        lambda cat: {"A": "-", "B": ":", "C": "--"}[cat],
        {"cat": Desc((), "auto")},
        {"linestyle": Desc((), "display")},
    ),
]

text_edges = [
    FuncEdge.from_func(
        "text",
        lambda j, cat: f"index={j[()]} class={cat!r}",
        {"j": Desc((), "auto"), "cat": Desc((), "auto")},
        {"text": Desc((), "display")},
    ),
    FuncEdge.from_func(
        "y",
        lambda j: j,
        {"j": Desc((), "auto")},
        {"y": Desc((), "data")},
    ),
    FuncEdge.from_func(
        "x",
        lambda: 2 * np.pi,
        {},
        {"x": Desc((), "data")},
    ),
    FuncEdge.from_func(
        "color",
        lambda: (0, 0, 0, 1),
        {},
        {"color": Desc((4,), "rgba")},
    ),
]


th = np.linspace(0, 2 * np.pi, 128)
delta = np.pi / 9

fig, nax = plt.subplots()

ax = CompatibilityAxes(nax)
nax.add_artist(ax)

for j in range(10):
    ac = ArrayContainer(
        **{
            "x": th,
            "y": np.sin(th + j * delta) + j,
            "j": np.asarray(j),
            "lw": np.asarray(j),
            "cat": {0: "A", 1: "B", 2: "C"}[j % 3],
        }
    )
    ax.add_artist(
        Line(
            ac,
            line_edges,
        )
    )
    ax.add_artist(
        Text(
            ac,
            text_edges,
            x=2 * np.pi,
            # ha="right",
            # bbox={"facecolor": "gray", "alpha": 0.5},
            antialiased=False,
            fontproperties=FontProperties(),
            rotation=0,
            alpha=1,
            usetex=False,
        )
    )
ax.set_xlim(0, np.pi * 2)
ax.set_ylim(-1.1, 10.1)

plt.show()

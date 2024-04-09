"""
=======================
Mapping Line Properties
=======================

Leveraging the converter functions to transform users space data to visualization data.

"""

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.colors import Normalize

from data_prototype.wrappers import FormattedText
from data_prototype.artist import CompatibilityArtist as CA
from data_prototype.line import Line
from data_prototype.containers import ArrayContainer
from data_prototype.description import Desc
from data_prototype.conversion_node import FunctionConversionNode
from data_prototype.conversion_edge import FuncEdge


cmap = plt.colormaps["viridis"]
cmap.set_over("k")
cmap.set_under("r")
norm = Normalize(1, 8)

line_edges = [
    FuncEdge.from_func(
        "lw",
        lambda lw: min(1 + lw, 5),
        {"lw": Desc((), str, "auto")},
        {"linewidth": Desc((), str, "display")},
    ),
    # Probably should separate out norm/cmap step
    # Slight lie about color being a string here, because of limitations in impl
    FuncEdge.from_func(
        "cmap",
        lambda j: cmap(norm(j)),
        {"j": Desc((), str, "auto")},
        {"color": Desc((), str, "display")},
    ),
    FuncEdge.from_func(
        "ls",
        lambda cat: {"A": "-", "B": ":", "C": "--"}[cat],
        {"cat": Desc((), str, "auto")},
        {"linestyle": Desc((), str, "display")},
    ),
]

text_converter = FunctionConversionNode.from_funcs(
    {
        "text": lambda j, cat: f"index={j[()]} class={cat!r}",
        "y": lambda j: j,
        "x": lambda x: 2 * np.pi,
    },
)


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
            "cat": {0: "A", 1: "B", 2: "C"}[j % 3],
        }
    )
    ax.add_artist(
        CA(
            Line(
                ac,
                line_edges,
            )
        )
    )
    ax.add_artist(
        FormattedText(
            ac,
            text_converter,
            x=2 * np.pi,
            ha="right",
            bbox={"facecolor": "gray", "alpha": 0.5},
        )
    )
ax.set_xlim(0, np.pi * 2)
ax.set_ylim(-1.1, 10.1)

plt.show()

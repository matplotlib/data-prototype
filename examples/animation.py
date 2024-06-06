"""
================
An animated line
================

An animated line using a custom container class,
:class:`.wrappers.LineWrapper`, and :class:`.wrappers.FormattedText`.

"""

import time
from typing import Dict, Tuple, Any, Union
from functools import partial

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from data_prototype.conversion_edge import Graph
from data_prototype.description import Desc

from data_prototype.conversion_node import FunctionConversionNode

from data_prototype.wrappers import FormattedText
from data_prototype.artist import CompatibilityArtist as CA
from data_prototype.line import Line


class SinOfTime:
    N = 1024
    # cycles per minutes
    scale = 10

    def describe(self):
        return {
            "x": Desc((self.N,)),
            "y": Desc((self.N,)),
            "phase": Desc(()),
            "time": Desc(()),
        }

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        th = np.linspace(0, 2 * np.pi, self.N)

        cur_time = time.time()

        phase = 2 * np.pi * (self.scale * cur_time % 60) / 60
        return {
            "x": th,
            "y": np.sin(th + phase),
            "phase": phase,
            "time": cur_time,
        }, hash(cur_time)


def update(frame, art):
    return art


sot_c = SinOfTime()
lw = CA(Line(sot_c, linewidth=5, color="green", label="sin(time)"))
fc = FormattedText(
    sot_c,
    FunctionConversionNode.from_funcs(
        {"text": lambda phase: f"ϕ={phase:.2f}", "x": lambda: 2 * np.pi, "y": lambda: 1}
    ),
    ha="right",
)
fig, ax = plt.subplots()
ax.add_artist(lw)
ax.add_artist(fc)
ax.set_xlim(0, 2 * np.pi)
ax.set_ylim(-1.1, 1.1)
ani = FuncAnimation(
    fig,
    partial(update, art=(lw, fc)),
    frames=25,
    interval=1000 / 60,
    # TODO: blitting does not work because wrappers do not inherent from Artist
    # blit=True,
)

plt.show()

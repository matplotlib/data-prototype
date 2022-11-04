"""
================
An animated line
================


"""
import time
from typing import Dict, Tuple, Any, Union
from functools import partial

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from data_prototype.containers import _Transform, Desc

from data_prototype.wrappers import LineWrapper, FormatedText


class SinOfTime:
    N = 1024
    # cycles per minutes
    scale = 10

    def describe(self):
        return {
            "x": Desc([self.N], float),
            "y": Desc([self.N], float),
            "phase": Desc([], float),
            "time": Desc([], float),
        }

    def query(
        self,
        transform: _Transform,
        size: Tuple[int, int],
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        th = np.linspace(0, 2 * np.pi, self.N)

        def next_time():
            cur_time = time.time()

            phase = 2 * np.pi * (self.scale * cur_time % 60) / 60
            return {
                "x": th,
                "y": np.sin(th + phase),
                "phase": phase,
                "time": cur_time,
            }, hash(cur_time)

        return next_time()


def update(frame, art):
    return art


sot_c = SinOfTime()
lw = LineWrapper(sot_c, lw=5, color="green", label="sin(time)")
fc = FormatedText(
    sot_c,
    {'text': lambda phase: f"ϕ={phase:.2f}"},
    x=2 * np.pi,
    y=1,
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

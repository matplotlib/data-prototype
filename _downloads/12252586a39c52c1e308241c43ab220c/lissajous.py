"""
==========================
An animated lissajous ball
==========================

Inspired by https://twitter.com/_brohrer_/status/1584681864648065027

An animated scatter plot using a custom container and :class:`.wrappers.PathCollectionWrapper`

"""

import time
from typing import Dict, Tuple, Any, Union
from functools import partial

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.markers as mmarkers
from matplotlib.animation import FuncAnimation

from mpl_data_containers.conversion_edge import Graph
from mpl_data_containers.description import Desc

from mpl_data_containers.wrappers import PathCollectionWrapper


class Lissajous:
    N = 1024
    # cycles per minutes
    scale = 2

    def describe(self):
        return {
            "x": Desc((self.N,)),
            "y": Desc((self.N,)),
            "time": Desc(()),
            "sizes": Desc(()),
            "paths": Desc(()),
            "edgecolors": Desc(()),
            "facecolors": Desc((self.N,)),
        }

    def query(
        self,
        graph: Graph,
        parent_coordinates: str = "axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        def next_time():
            cur_time = time.time()
            cur_time = np.array(
                [cur_time, cur_time - 0.1, cur_time - 0.2, cur_time - 0.3]
            )

            phase = 15 * np.pi * (self.scale * cur_time % 60) / 150
            marker_obj = mmarkers.MarkerStyle("o")
            return {
                "x": np.cos(5 * phase),
                "y": np.sin(3 * phase),
                "sizes": np.array([256]),
                "paths": [
                    marker_obj.get_path().transformed(marker_obj.get_transform())
                ],
                "edgecolors": "k",
                "facecolors": ["#4682b4ff", "#82b446aa", "#46b48288", "#8246b433"],
                "time": cur_time[0],
            }, hash(cur_time[0])

        return next_time()


def update(frame, art):
    return art


sot_c = Lissajous()

fig, ax = plt.subplots()
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.1, 1.1)
lw = PathCollectionWrapper(sot_c, offset_transform=ax.transData)
ax.add_artist(lw)
# ax.set_xticks([])
# ax.set_yticks([])
ax.set_aspect(1)
ani = FuncAnimation(
    fig,
    partial(update, art=(lw,)),
    frames=60,
    interval=1000 / 100 * 15,
    # TODO: blitting does not work because wrappers do not inherent from Artist
    # blit=True,
)
plt.show()

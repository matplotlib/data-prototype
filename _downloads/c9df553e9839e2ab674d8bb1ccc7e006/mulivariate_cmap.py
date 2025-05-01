"""
=========================
Custom bivariate colormap
=========================


Using ``nu`` functions to account for two values when computing the color
of each pixel.
"""

import matplotlib.pyplot as plt
import numpy as np

from mpl_data_containers.image import Image
from mpl_data_containers.artist import CompatibilityAxes
from mpl_data_containers.description import Desc
from mpl_data_containers.containers import FuncContainer
from mpl_data_containers.conversion_edge import FuncEdge

from matplotlib.colors import hsv_to_rgb


def func(x, y):
    return (
        (np.sin(x).reshape(1, -1) * np.cos(y).reshape(-1, 1)) ** 2,
        np.arctan2(np.cos(y).reshape(-1, 1), np.sin(x).reshape(1, -1)),
    )


def image_nu(image):
    saturation, angle = image
    hue = (angle + np.pi) / (2 * np.pi)
    value = np.ones_like(hue)
    return np.clip(hsv_to_rgb(np.stack([hue, saturation, value], axis=2)), 0, 1)


fc = FuncContainer(
    {},
    xyfuncs={
        "x": ((2,), lambda x, y: [x[0], x[-1]]),
        "y": ((2,), lambda x, y: [y[0], y[-1]]),
        "image": (("N", "M", 2), func),
    },
)

image_edges = FuncEdge.from_func(
    "image",
    image_nu,
    {"image": Desc(("M", "N", 2), "auto")},
    {"image": Desc(("M", "N", 3), "rgb")},
)

im = Image(fc, [image_edges])

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
ax.add_artist(im)
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
plt.show()

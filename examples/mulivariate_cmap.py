"""
=========================
Custom bivariate colormap
=========================


Using ``nu`` functions to account for two values when computing the color
of each pixel.
"""

import matplotlib.pyplot as plt
import numpy as np

from data_prototype.wrappers import ImageWrapper
from data_prototype.containers import FuncContainer
from data_prototype.conversion_node import FunctionConversionNode

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
        "xextent": ((2,), lambda x, y: [x[0], x[-1]]),
        "yextent": ((2,), lambda x, y: [y[0], y[-1]]),
        "image": (("N", "M", 2), func),
    },
)

im = ImageWrapper(fc, FunctionConversionNode.from_funcs("bivariate", {"image": image_nu}))

fig, ax = plt.subplots()
ax.add_artist(im)
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
plt.show()

"""
=====================
A functional 2D image
=====================

A 2D image generated using :class:`.containers.FuncContainer` and
:class:`wrappers.ImageWrapper`.
"""

import matplotlib.pyplot as plt
import numpy as np

from data_prototype.wrappers import ImageWrapper
from data_prototype.containers import FuncContainer

import matplotlib as mpl
from matplotlib.colors import Normalize


fc = FuncContainer(
    {},
    xyfuncs={
        "xextent": ((2,), lambda x, y: [x[0], x[-1]]),
        "yextent": ((2,), lambda x, y: [y[0], y[-1]]),
        "image": (("N", "M"), lambda x, y: np.sin(x).reshape(1, -1) * np.cos(y).reshape(-1, 1)),
    },
)
cmap = mpl.colormaps["viridis"]
norm = Normalize(-1, 1)
im = ImageWrapper(fc, {"image": lambda image: cmap(norm(image))})

fig, ax = plt.subplots()
ax.add_artist(im)
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
fig.colorbar(im)
plt.show()

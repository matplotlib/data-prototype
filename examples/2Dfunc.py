"""
=====================
A functional 2D image
=====================


"""

import matplotlib.pyplot as plt
import numpy as np

from data_prototype.wrappers import ImageWrapper
from data_prototype.containers import FuncContainer

from matplotlib.colors import Normalize

fc = FuncContainer(
    {},
    xyfuncs={
        "extent": lambda x, y: [x[0], x[-1], y[0], y[-1]],
        "image": lambda x, y: np.sin(x).reshape(1, -1) * np.cos(y).reshape(-1, 1),
    },
)
im = ImageWrapper(fc, norm=Normalize(-1, 1))

fig, ax = plt.subplots()
ax.add_artist(im)
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
fig.colorbar(im)
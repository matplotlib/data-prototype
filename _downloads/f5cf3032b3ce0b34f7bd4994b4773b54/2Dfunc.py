"""
=====================
A functional 2D image
=====================

A 2D image generated using :class:`.containers.FuncContainer` and
:class:`wrappers.ImageWrapper`.
"""

import matplotlib.pyplot as plt
import numpy as np

from mpl_data_containers.artist import CompatibilityAxes
from mpl_data_containers.image import Image
from mpl_data_containers.containers import FuncContainer

from matplotlib.colors import Normalize


fc = FuncContainer(
    {},
    xyfuncs={
        "x": ((2,), lambda x, y: [x[0], x[-1]]),
        "y": ((2,), lambda x, y: [y[0], y[-1]]),
        "image": (
            ("N", "M"),
            lambda x, y: np.sin(x).reshape(1, -1) * np.cos(y).reshape(-1, 1),
        ),
    },
)
norm = Normalize(vmin=-1, vmax=1)
im = Image(fc, norm=norm)

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)

ax.add_artist(im)
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
# fig.colorbar(im, ax=nax)
plt.show()

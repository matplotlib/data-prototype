"""
===================================
(Infinitly) Zoomable Mandelbrot Set
===================================

A mandelbrot set which is computed using a :class:`.containers.FuncContainer`
and represented using a :class:`wrappers.ImageWrapper`.

The mandelbrot recomputes as it is zoomed in and/or panned.

"""

import matplotlib.pyplot as plt
import numpy as np

from mpl_data_containers.artist import CompatibilityAxes
from mpl_data_containers.image import Image
from mpl_data_containers.containers import FuncContainer

from matplotlib.colors import Normalize

maxiter = 75


def mandelbrot_set(X, Y, maxiter, *, horizon=3, power=2):
    C = X + Y[:, None] * 1j
    N = np.zeros_like(C, dtype=int)
    Z = np.zeros_like(C)
    for n in range(maxiter):
        mask = abs(Z) < horizon
        N += mask
        Z[mask] = Z[mask] ** power + C[mask]
    N[N == maxiter] = -1
    return Z, N


fc = FuncContainer(
    {},
    xyfuncs={
        "x": ((2,), lambda x, y: [x[0], x[-1]]),
        "y": ((2,), lambda x, y: [y[0], y[-1]]),
        "image": (("N", "M"), lambda x, y: mandelbrot_set(x, y, maxiter)[1]),
    },
)
cmap = plt.get_cmap()
cmap.set_under("w")
im = Image(fc, norm=Normalize(0, maxiter), cmap=cmap)

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
ax.add_artist(im)
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)

nax.set_aspect("equal")  # No equivalent yet

plt.show()

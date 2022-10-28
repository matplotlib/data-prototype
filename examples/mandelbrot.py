"""
===================================
(Infinitly) Zoomable Mandelbrot Set
===================================


"""

import matplotlib.pyplot as plt
import numpy as np

from data_prototype.wrappers import ImageWrapper
from data_prototype.containers import FuncContainer

from matplotlib.colors import Normalize

maxiter = 75


def mandelbrot_set(X, Y, maxiter, *, horizon=3, power=2):
    C = X + Y[:, None] * 1j
    N = np.zeros_like(C, dtype=int)
    Z = np.zeros_like(C)
    for n in range(maxiter):
        I = abs(Z) < horizon
        N += I
        Z[I] = Z[I] ** power + C[I]
    N[N == maxiter] = -1
    return Z, N


fc = FuncContainer(
    {},
    xyfuncs={
        "xextent": ((2,), lambda x, y: [x[0], x[-1]]),
        "yextent": ((2,), lambda x, y: [y[0], y[-1]]),
        "image": (("N", "M"), lambda x, y: mandelbrot_set(x, y, maxiter)[1]),
    },
)
cmap = plt.get_cmap()
cmap.set_under("w")
im = ImageWrapper(fc, norm=Normalize(0, maxiter), cmap=cmap)

fig, ax = plt.subplots()
ax.add_artist(im)
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_aspect("equal")
fig.colorbar(im)
plt.show()

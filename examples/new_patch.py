"""
======
Circle
======

Example of directly creating a Patch artist that is defined by a
x, y, and path codes.


"""

import matplotlib.pyplot as plt


from mpl_data_containers.artist import CompatibilityAxes
from mpl_data_containers.patches import Patch
from mpl_data_containers.containers import ArrayContainer

from matplotlib.path import Path

c = Path.unit_circle()

sc = ArrayContainer(None, x=c.vertices[:, 0], y=c.vertices[:, 1], codes=c.codes)
lw2 = Patch(sc, linewidth=3, linestyle=":", edgecolor="C5", alpha=1, hatch=None)

fig, nax = plt.subplots()
nax.set_aspect("equal")
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
ax.add_artist(lw2, 2)
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.1, 1.1)

plt.show()

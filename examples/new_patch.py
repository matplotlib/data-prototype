"""
Example of directly creating a Patch artist that is defined by a Path
"""

import matplotlib.pyplot as plt
import numpy as np


from data_prototype.artist import CompatibilityAxes
from data_prototype.patches import Patch
from data_prototype.containers import ArrayContainer

from matplotlib.path import Path

c = Path.unit_circle()

sc = ArrayContainer(None, x=c.vertices[:, 0], y=c.vertices[:, 1], codes=c.codes)
lw2 = Patch(sc, linewidth=3, linestyle=":", edgecolor="C5", alpha=1, hatch=None)

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
ax.add_artist(lw2, 2)
ax.set_xlim(0, np.pi * 4)
ax.set_ylim(-1.1, 1.1)

plt.show()

"""
======================
A re-binning histogram
======================

A :class:`.containers.HistContainer` which is used with :class:`.wrappers.StepWrapper`
to provide a histogram which recomputes the bins based on a range selected.
"""

import matplotlib.pyplot as plt
import numpy as np

from mpl_data_containers.wrappers import StepWrapper
from mpl_data_containers.containers import HistContainer

hc = HistContainer(
    np.concatenate([np.random.randn(5000), 0.1 * np.random.randn(500) + 5]), 25
)


fig, (ax1, ax2) = plt.subplots(1, 2, layout="constrained")
for ax in (ax1, ax2):
    ax.add_artist(StepWrapper(hc, lw=0, color="green"))
    ax.set_ylim(0, 1)

ax1.set_xlim(-7, 7)
ax1.axvspan(4.5, 5.5, facecolor="none", zorder=-1, lw=5, edgecolor="k")
ax1.set_title("full range")

ax2.set_xlim(4.5, 5.5)
ax2.set_title("zoom to small peak")


plt.show()

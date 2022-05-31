"""
=================
A functional line
=================

The hello-world
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data_prototype.wrappers import LineWrapper
from data_prototype.containers import FuncContainer, SeriesContainer

fc = FuncContainer({"x": (["N"], lambda x: x), "y": (["N"], np.sin)})
lw = LineWrapper(fc, lw=5, color="green", label="sin (function)")

th = np.linspace(0, 2 * np.pi, 16)
sc = SeriesContainer(pd.Series(index=th, data=np.cos(th)), index_name="x", col_name="y")
lw2 = LineWrapper(sc, lw=3, color="blue", label="cos (pandas)")

fig, ax = plt.subplots()
ax.add_artist(lw)
ax.add_artist(lw2)
ax.set_xlim(0, np.pi * 4)
ax.set_ylim(-1.1, 1.1)

plt.show()

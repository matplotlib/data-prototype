"""
=================
A functional line
=================

The hello-world
"""

import matplotlib.pyplot as plt
import numpy as np

from data_prototype.wrappers import LineWrapper
from data_prototype.containers import FuncContainer

fc = FuncContainer({'x': lambda x: x, 'y': lambda x: np.sin(x)})
lw = LineWrapper(fc, lw=5, color='green')

fig, ax = plt.subplots()
ax.add_artist(lw)
ax.set_xlim(0, np.pi * 2)
ax.set_ylim(-1.1, 1.1)

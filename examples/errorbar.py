"""
=================
Show data frame
=================

The hello-world
"""

import matplotlib.pyplot as plt
import numpy as np


from data_prototype.wrappers import ErrorbarWrapper
from data_prototype.containers import ArrayContainer

x = np.arange(10)
y = x**2
yupper = y + np.sqrt(y)
ylower = y - np.sqrt(y)
xupper = x + 0.5
xlower = x - 0.5

ac = ArrayContainer(x=x, y=y, yupper=yupper, ylower=ylower, xlower=xlower, xupper=xupper)


fig, ax = plt.subplots()

ew = ErrorbarWrapper(ac)
ax.add_artist(ew)
ax.set_xlim(0, 10)
ax.set_ylim(0, 100)
plt.show()

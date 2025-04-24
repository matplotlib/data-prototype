"""
=========================================
An simple scatter plot using `ax.scatter`
=========================================

This is a quick comparison between the current Matplotlib `scatter` and
the version in :file:`mpl_data_containers/axes.py`, which uses data containers
and a conversion pipeline.

This is here to show what does work and what does not work with the current
implementation of container-based artist drawing.
"""

import mpl_data_containers.axes  # side-effect registers projection # noqa

import matplotlib.pyplot as plt

fig = plt.figure()
newstyle = fig.add_subplot(2, 1, 1, projection="mpl-data-containers")
oldstyle = fig.add_subplot(2, 1, 2)

newstyle.scatter([0, 1, 2], [2, 5, 1])
oldstyle.scatter([0, 1, 2], [2, 5, 1])
newstyle.scatter([0, 1, 2], [3, 1, 2])
oldstyle.scatter([0, 1, 2], [3, 1, 2])


# Autoscaling not working
newstyle.set_xlim(oldstyle.get_xlim())
newstyle.set_ylim(oldstyle.get_ylim())

plt.show()

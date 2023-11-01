import data_prototype.axes  # side-effect registers projection # noqa

import matplotlib.pyplot as plt

fig = plt.figure()
newstyle = fig.add_subplot(2, 1, 1, projection="data-prototype")
oldstyle = fig.add_subplot(2, 1, 2)

newstyle.scatter([0, 1, 2], [2, 5, 1])
oldstyle.scatter([0, 1, 2], [2, 5, 1])
newstyle.scatter([0, 1, 2], [3, 1, 2])
oldstyle.scatter([0, 1, 2], [3, 1, 2])


# Autoscaling not working
newstyle.set_xlim(oldstyle.get_xlim())
newstyle.set_ylim(oldstyle.get_ylim())

plt.show()

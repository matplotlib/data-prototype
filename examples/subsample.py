"""
====================
Dynamic Downsampling
====================

Generates a large image with three levels of detail.

When zoomed out, appears as a difference of 2D Gaussians.
At medium zoom, a diagonal sinusoidal pattern is apparent.
When zoomed in close, noise is visible.

The image is dynamically subsampled using a local mean which hides the finer details.
"""

from typing import Tuple, Dict, Any, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

import numpy as np

from mpl_data_containers.description import Desc, desc_like
from mpl_data_containers.artist import CompatibilityArtist as CA
from mpl_data_containers.image import Image
from mpl_data_containers.containers import ArrayContainer

from skimage.transform import downscale_local_mean


x = y = np.linspace(-3, 3, 3000)
X, Y = np.meshgrid(x, y)
Z1 = np.exp(-(X**2) - Y**2) + 0.08 * np.sin(50 * (X + Y))
Z2 = np.exp(-((X - 1) ** 2) - (Y - 1) ** 2)
Z = (Z1 - Z2) * 2

Z += np.random.random(Z.shape) - 0.5


class Subsample:
    def describe(self):
        return {
            "x": Desc((2,)),
            "y": Desc((2,)),
            "image": Desc(("M", "N")),
        }

    def query(
        self,
        graph,
        parent_coordinates="axes",
    ) -> Tuple[Dict[str, Any], Union[str, int]]:
        desc = Desc(("N",), coordinates="data")
        xy = {"x": desc, "y": desc}
        data_lim = graph.evaluator(xy, desc_like(xy, coordinates="axes")).inverse

        pts = data_lim.evaluate({"x": (0, 1), "y": (0, 1)})
        x1, x2 = pts["x"]
        y1, y2 = pts["y"]

        xi1 = np.argmin(np.abs(x - x1))
        yi1 = np.argmin(np.abs(y - y1))
        xi2 = np.argmin(np.abs(x - x2))
        yi2 = np.argmin(np.abs(y - y2))

        xscale = int(np.ceil((xi2 - xi1) / 50))
        yscale = int(np.ceil((yi2 - yi1) / 50))

        return {
            "x": [x1, x2],
            "y": [y1, y2],
            "image": downscale_local_mean(Z[xi1:xi2, yi1:yi2], (xscale, yscale)),
        }, hash((x1, x2, y1, y2))


non_sub = ArrayContainer(**{"image": Z, "x": np.array([0, 1]), "y": np.array([0, 10])})

sub = Subsample()
cmap = mpl.colormaps["coolwarm"]
norm = Normalize(-2.2, 2.2)
im = Image(sub, cmap=cmap, norm=norm)

fig, ax = plt.subplots()
ax.add_artist(CA(im))
ax.set_xlim(-3, 3)
ax.set_ylim(-3, 3)
plt.show()

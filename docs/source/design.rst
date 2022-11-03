========
 Design
========

When a Matplotlib :obj:`~matplotlib.artist.Artist` object in rendered via the `~matplotlib.artist.Artist.draw` method the following
steps happen (in spirit but maybe not exactly in code):

1. get the data
2. convert from unit-full to unit-less data
3. convert the unit-less data from user-space to rendering-space
4. call the backend rendering functions

..
   If we were to call these steps :math:`f_1` through :math:`f_4` this can be expressed as (taking
   great liberties with the mathematical notation):

   .. math::

      R = f_4(f_3(f_2(f_1())))

   or if you prefer

   .. math::

      R  = (f_4 \circ f_3 \circ f_2 \circ f_1)()

   It is reasonable that if we can do this for one ``Artist``, we can build up
   more complex visualizations by rendering multiple ``Artist`` to the same
   target.

However, this clear structure is frequently elided and obscured in the
Matplotlib code base: Step 3 is only present for *x* and *y* like data (encoded
in the `~matplotlib.transforms.TransformNode` objects) and color mapped data
(implemented in the `.matplotlib.colors.ScalarMappable` family of classes); the
application of Step 2 is inconsistent (both in actual application and when it
is applied) between artists; each ``Artist`` stores it's data in its own way
(typically as numpy arrays).

With this view, we can understand the `~matplotlib.artist.Artist.draw` methods
to be very extensively `curried
<https://en.wikipedia.org/wiki/Curry_(programming_language)>`__ version of
these function chains where the objects allow us to modify the arguments to the
functions.

The goal of this work is to bring this structure more the foreground in the internal of
Matplotlib to make it easier to reason about, easier to extend, and easier to inject
custom logic at each of the steps

A paper with the formal mathematical description of these ideas is in
preparation.

Data pipeline
=============

Get the data (Step 1)
---------------------

Currently, almost all ``Artist`` class store the data associated with them as
attributes on the instances as `numpy.array` objectss.  On one hand, this can
be very useful as historically data was frequently already in `numpy.array`
objects and, if you know the right methods for *this* ``Artist`` you can access
that state to update or query it.  From a certain point of view, this is
consistent with the scheme laid out above as ``self.x[:]`` is really
``self.x.__getitem__(slice())`` which is (technically) a function call.

However, this has several drawbacks.  In most cases the data attributes on an
``Artist`` are closely linked -- the *x* and *y* on a
`~matplotlib.lines.Line2D` must be the same length -- and by storing them
separately it is possible that they will get out of sync in problematic ways.
Further, because the data is stored as materialized ``numpy`` arrays, there we
must decide before draw time what the correct sampling of the data is.  While
there are some projects like `grave <https://networkx.org/grave/>`__ that wrap
richer objects or `mpl-modest-image
<https://github.com/ChrisBeaumont/mpl-modest-image>`__, `datashader
<https://datashader.org/getting_started/Interactivity.html#native-support-for-matplotlib>`__,
and `mpl-scatter-density <https://github.com/astrofrog/mpl-scatter-density>`__
that dynamically re-sample the data these are niche libraries.

The first goal of this project is to bring support for draw-time resampleing to
every Matplotlib ``Artist`` out of the box.  The current approach is to move
all of the data storage off of the ``Artist`` directly and into a (so-called)
`~data_prototype.containers.DataContainer` instance.  The primary method on these objects
is the `~data_prototype.containers.DataContainer.query` method which has the signature ::

    def query(
        self,
        transform: _Transform,
        size: Tuple[int, int],
    ) -> Tuple[Dict[str, Any], Union[str, int]]:

The query is passed in:

- A transform from "Axes" to "data" (using Matplotlib's names for the `various
  coordinate systems
  <https://matplotlib.org/stable/tutorials/advanced/transforms_tutorial.html>`__
- A notion of how big the axes is in "pixels" to provide guidance on what the correct number
  of samples to return is.

It will return:

- A mapping of strings to things that is coercible (with the help of the
  functions is steps 2 and 3) to a numpy array or types understandable by the
  backends.
- A key that can be used for caching

This function will be called at draw time by the ``Aritist`` to get the data to
be drawn.  In the simplest cases
(e.g. `~data_prototype.containers.ArrayContainer` and
`~data_prototype.containers.DataFrameContainer`) the ``query`` method ignores
the input and returns the data as-is.  However, based on these inputs it is
possible for the ``query`` method to get the data limits, even sampling in
screen space, and an approximate estimate of the resolution of the
visualization.  This also opens up several interesting possibilities:

1. "Pure function" containers (such as
   `~data_prototype.containers.FuncContainer`) which will dynamically sample a
   function at "a good resolution" for the current data limits and screen size.
2. A "resampling" container that either down-samples or slices the data it holds based on
   the current view limits.
3. A container that makes a network or database call and automatically refreshes the data
   as a function of time.
4. Containers that do binning or aggregation of the user data (such as
   `~data_prototype.containers.HistContainer`).

By accessing all of the data that is needed in draw in a single function call
the ``DataContainer`` instances can ensure that the data is coherent and
consistent.  This is important for applications like steaming where different
parts of the data may be arriving at different rates and it would thus be the
``DataContainer``'s responsibility to settle any race conditions and always
return aligned data to the ``Artist``.


There is still some ambiguity as to what should be put in the data.  For
example with `~matplotlib.lines.Line2D` it is clear that the *x* and *y* data
should be pulled from the ``DataConatiner``, but things like *color* and
*linewidth* are ambiguous.  A later section will make the case that it should be
possible, but maybe not required, that these values be accessible in the data
context.

An additional task that the ``DataContainer`` can do is to describe the type,
shape, fields, and topology of the data it contains.  For example a
`~matplotlib.lines.Line2D` needs an *x* and *y* that are the same length, but
`~matplotlib.patches.StepPatch` (which is also a 2D line) needs a *x* that is
one longer than the *y*.  The difference is that a ``Line2D`` in points with
values which can be continuously interpolated between and ``StepPatch`` is bin
edges with a constant value between the edges.  This design lets us make
explicit the implicit encoding of this sort of distinction in Matplotlib and be
able to programatically operate on it.  The details of exactly how to encode
all of this still needs to be developed.  There is a
`~data_prototype.containers.DataContainer.describe` method, however it is the
most provisional part of the current design.


Unit conversion (Step 2)
------------------------

Real data almost always has some units attached to it.  Historically, this
information can be carried "out of band" in the structure of the code or in
custom containers or data types that are unit-aware.  The recent work on ``numpy`` to
make ``np.dtype`` more easily extendable is likely to make unit-full data much more
common and easier to work with in the future.

In principle the user should be able to plot sets of data, one of them in *ft*
the other in *m* and then show the ticks in *in* and then switch to *cm* and
have everything "just work" for all plot types.  Currently we are very far from
this due to some parts of the code eagerly converting to the unit-less
representation and not keeping the original, some parts of the code failing to
do the conversion at all, some parts doing the conversion after coercing to
``numpy`` and losing the unit information, etc.  Further, because the data
access and processing pipeline is done differently in every ``Artist`` it is a
constant game of whack-a-bug to keep this working.  If we adopt the consistent
``DataContainer`` model for accessing the data and call
`~data_prototype.containers.DataContainer.query` at draw time we will have a
consistent place to also do the unit conversion.

The ``DataContainer`` can also carry inspectable information about what the
units of its data are in which would make it possible to do ahead-of-time
verification that the data of all of the ``Artists`` in an ``Axes`` are
consistent with unit converters on the ``Axis``.


Convert for rendering (Step 3)
------------------------------

The next step is to get the data from unit-less "user data" into something that
the backend renderer understand.  This can range from coordinate
transformations (as with the ``Transfrom`` stack operations on *x* and *y* like
values), representation conversions (like named colors to RGB values), mapping
stings to a set of objects (like named markershape), to paraaterized type
conversion (like colormapping).  Although Matplotlib is currently doing all of
these conversions, the user really only has control of the position and
colormapping (on `~matplotlib.colors.ScalarMappable` sub-classes).  The next
thing that this design allows is for user defined functions to be passed for
any of the relevant data fields.

This will open up paths to do a number of nice things such as multi-variate
color maps, lines who's width and color vary along their length, constant but
parameterized colors and linestyles, and a version of ``scatter`` where the
marker shape depends on the data.  All of these things are currently possible
in Matplotlib, but require significant work before calling Matplotlib and can
be very difficult to update after the fact.

Pass to backend (Step 4)
------------------------

This part of the process is proposed to remain unchanged from current
Matplotlib.  The calls to the underlying ``Renderer`` objects in ``draw``
methods have stood the test of time and changing them is out of scope for the
current work.  In the future we may want to consider eliding Steps 3 and 4 in
some cases for performance reasons to be able push the computation down to a
GPU.


Caching
=======

A key to keeping this implementation efficient is to be able to cache when we
have to re-compute values.  Internally current Matplotlib has a number of
ad-hoc caches, such as in ``ScalarMappable`` and ``Line2D``.  Going down the
route of hashing all of the data is not a sustainable path (in the case even
modestly sized data the time to hash the data will quickly out-strip any
possible time savings doing the cache lookup!).  The proposed ``query`` method
returns a cache key that it generates to the caller.  The exact details of how
to generate that key are left to the ``DataContainer`` implementation, but if
the returned data changed, then the cache key must change.  The cache key
should be computed from a combination of the ``DataContainers`` internal state,
the transform and size passed in.

The choice to return the data and cache key in one step, rather than be a two
step process is drive by simplicity and because the cache key is computed
inside of the ``query`` call.  If computing the cache key is fast and the data
to be returned in "reasonable" for the machine Matplotlib is running on (it
needs to be or we won't render!), then if it makes sense to cache the results
it can be done by the ``DataContainer`` and returned straight away along with
the computed key.

There will need to be some thought put into cache invalidation and size
management at the ``Artist`` layer.  We also need to determine how many cache
layers to keep. Currently only the results of Step 3 are cached, but we may
want to additionally cache intermediate results after Step 2.  The caching from
Step 1 is likely best left to the ``DataContainer`` instances.

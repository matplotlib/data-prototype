Containers Design Choices
=========================

``Callable`` vs ``class``
-------------------------

In the mathematical formulation we model the date source as a function, however
in the implementation this has been promoted to a full class with two methods
of ``query`` and ``describe``.

The justification for this is:

1. We anticipate the need to update the data held by the container so will
   likely be backed by instances of classes in practice
2. We will want the containers to provide a static type and shape information
   about itself.  In principle this could be carried in the signature of the
   function, but Python's built in type system is too dynamic for this to be
   practical.

A `collections.SimpleNamespace` with the correct names is compatible with this API.


``obj.__call__`` and ``obj.describe`` would make the data feel more like a
function, however if someone wanted to implement this with a function rather
than a class it would require putting a callable as an attribute on a callable.
This is technically allowed in Python, but a bit weird.

Caching design
--------------

.. note::

   There are two hard problems in computer science:

   1. naming things
   2. cache invalidation
   3. off-by-one bugs

Because we are adding a layer of indirection to the data access it is no longer
generally true that "getting the data" is cheap nor that any layer of the
system has all of the information required to know if cached values are still
valid.

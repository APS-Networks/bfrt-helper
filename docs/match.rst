bfrt_helper.match
=================

.. contents:: :local:
   :depth: 3

.. currentmodule:: bfrt_helper.match

There are two match types that can be considered in terms of a mask and a
value, :ref:`Longest Prefix Match`, and :ref:`Ternary`.

In turn, each of these can be thought in the context of sets: the set of all
possible values within either are the bits selected for matching, and every
combination of the remaining 'don't care' bits.

It is therefore possible to apply set operations, the relevant of which
being:

* Whether an expression is a superset/subset of another; and,
* Calculating the intersection of two sets (all the values common to both); and,
* The union of two sets (all values from both sets); and,
* Whether or not two sets overlap.




Base Match Type
***************

Masked
^^^^^^

.. autoclass:: Masked
   :members:


Supported Types
***************


Exact
^^^^^^^^^^^^^^^^

.. autoclass:: Exact
   :members:
   :inherited-members:

Longest Prefix Match
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: LPM
   :members:
   :inherited-members:


Ternary
^^^^^^^^^^^^^^^^

.. autoclass:: Ternary
   :members:
   :inherited-members:



Exceptions
**********

MismatchedKeys
^^^^^^^^^^^^^^
.. autoclass:: MismatchedKeys

MismatchedTypes
^^^^^^^^^^^^^^^
.. autoclass:: MismatchedTypes






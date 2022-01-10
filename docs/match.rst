Match
-----

.. contents:: :local:
   :depth: 3

.. currentmodule:: bfrt_helper.match

There are two match types that can be considered in terms of a mask and a
value, :ref:`LongestPrefixMatch`, and :ref:`Ternary`.

In turn, each of these can be thought in the context of sets: the set of all
possible values within either are the bits selected for matching, and every
combination of the remaining 'don't care' bits.

It is therefore possible to apply set operations, the relevant of which
being:

* Whether an expression is a superset/subset of another; and,
* Calculating the intersection of two sets (all the values common to both); and,
* The union of two sets (all values from both sets); and,
* Whether or not two sets overlap.




Exact
^^^^^
An exact match is exactly what it sounds like. In a key field, any comparison
must on a :ref:`Field` must match **exactly.**

API reference: :ref:`Exact<bfrt_info.match.Exact>`

Masked Matches
^^^^^^^^^^^^^^

A masked match is one that can be expressed in terms of a value and a mask,
which applies to :ref:`Ternary` and :ref:`Longest Prefix Match` expressions.

Longest Prefix Match
********************

API reference: :ref:`LongestPrefixMatch`

Ternary
*******

API reference: :ref:`Ternary`


Unsupported Matches
^^^^^^^^^^^^^^^^^^^
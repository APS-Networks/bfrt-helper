Match
-----

.. contents:: :local:
   :depth: 3

.. currentmodule:: bfrt_helper

The term match can apply in two different contexts; in the context of a single
field where match type is applied to some field value; and, where a match is
comprised of multiple match types and values.

It is the difference between:

.. code:: python

   field_match = Exact(Port(80))

and:

.. code:: python

   match = Match({
      'hdr.tcp.dstPort': Exact(Port(80)),
      'hdr.ip.srcAddr': Exact(IPv4Address('192.168.0.1'))
   })

There are two match types that can be considered in terms of a mask and a
value, :py:class:`~match.LongestPrefixMatch`, and :py:class:`~match.Ternary`.

In turn, each of these can be thought in the context of sets: the set of all
possible values within either are the bits selected for matching, and every
combination of the remaining 'don't care' bits.






Exact
^^^^^
An exact match is exactly what it sounds like. In a key field, any comparison
must on a :py:class:`~fields.Field` must match **exactly.**

.. rubric:: API References


* :py:class:`~match.Exact`

Masked Matches (LPM & Ternary)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A masked match is one that can be expressed in terms of a value and a mask,
which applies to :py:class:`~match.Ternary` and :py:class:`~match.LongestPrefixMatch`
expressions.

Masked :py:class:`~match.Ternary` expressions have a mask which indicates which bits
in the value are to be considered when performing comparisons.

.. note::
   In this library, a mask bit value of ``1`` indicates that the bit in the same
   location in the value is to be considered as a part of the mask. This is the
   same as mask expressions in P4, and will be familiar to anyone who has defined
   IP networks (e.g. ``192.168.0.0, 255.255.255.0``).

.. note::
   Masked matches have exact equivalents; they are where the mask is all
   1's. With LPM, this is equivalent when a prefix is the same length as the
   number of bits in the value, as defined by it's :py:class:`~fields.Field`.


A ternary expression's mask bits can be set arbitrarily across the mask.
A :py:class:`~match.LongestPrefixMatch` on the other hand will have bits set
contiguously up to it's "prefix length".

Consequently, these match kinds share a common set of bitwise and mathematical
operations. For exposition, we'll use an :py:class:`~fields.IPv4Address` to
this.

Construction
************

Construction is as follows:

.. code:: python

   # Ternary

   ternary = Ternary(
      value=IPv4Address('192.168.0.0'),
      mask=IPv4Address('255.255.255.0'))

   # The value keyword can be omitted, as can the constructor call of the mask.
   # The mask value, if not the same type as the value, an attempt will be made
   # to construct the mask using the value's type:

   ternary = Ternary(IPv4Address('192.168.0.0'), mask='255.255.255.0')

   # LPM

   lpm = LongestPrefixMatch(value=IPv4Address('192.168.0.0'), prefix=24)

   # As with the ternary expression, the value keyword can be ommitted:

   lpm = LongestPrefixMatch(IPv4Address('192.168.0.0'), prefix=24)


Omitting the mask will yield an object which is equivalent to an exact match,
i.e., all the mask bits are set. However, with :py:class:`match.Ternary`
objects, you can supply a boolean ``dont_care`` value which, if ``True``, will
yield an object with none of the mask bits set. This is important when used in
the context of a key, where you might not care about matching on that specific
field.

.. code:: python

   ternary = Ternary(IPv4Address('192.168.0.0'))

   # print(ternary) will yield "192.168.0.0 &&& 255.255.255.255"

   ternary = Ternary(IPv4Address('192.168.0.0'), dont_care=True)

   # print(ternary) will yield "192.168.0.0 &&& 0.0.0.0"


Operations
**********

The interesting thing about masked matches is that, for some operations, they
can be considered in the contexts of sets. For example, it should be fairly
obvious that the IP subnet ``192.168.0.0/24`` contains all the IP addresses
beginning with ``192.168.0...``

We can can compare on the basis of (proper?) superset/subset and intersections,
detect overlaps, but we cannot make unions.

See the following for more information:

* :py:meth:`~bfrt_helper.match.Masked.subset_of`: ``<=``
* :py:meth:`~bfrt_helper.match.Masked.superset_of`: ``>=``
* :py:meth:`~bfrt_helper.match.Masked.proper_subset_of`: ``<``
* :py:meth:`~bfrt_helper.match.Masked.proper_superset_of`: ``>``
* :py:meth:`~bfrt_helper.match.Masked.intersection`: ``&``
* :py:meth:`~bfrt_helper.match.Masked.merged`
* :py:meth:`~bfrt_helper.match.Masked.overlaps`




.. rubric:: API References

* :py:class:`~match.LongestPrefixMatch`
* :py:class:`~match.Ternary`



Unsupported Matches
^^^^^^^^^^^^^^^^^^^

Currently, only Exact, LPM and Ternary expressions are supported.
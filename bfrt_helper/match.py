from bfrt_helper.util import InvalidOperation
from bfrt_helper.util import InvalidValue
from bfrt_helper.util import mask_from_prefix
from bfrt_helper.fields import Field
from bfrt_helper.fields import IPv4Address
from bfrt_helper.fields import MismatchedTypes


class MismatchedKeys(Exception):
    """Raised when the key's name doesn't match when comparing two match
    objects
    """

    def __init__(self, message):
        super().__init__(message)


class Masked:
    """Base class for all matches which can be represented in terms of a value
    and a mask.

    """

    def __init__(self):
        self.value = None
        self.mask = None

    def subset_of(self, other: "Masked") -> bool:
        """Compares with another match, where ``self`` is found to be a subset
        of the other, that is to say; for all :math:`x` in set :math:`B`,
        there exists some element :math:`x` in set :math:`A`.

        A set is a subset of itself.

        Args:

            other (Masked): Other masked value to compare against.

        Returns:

            bool: True if ``self`` is subset of ``other``
        """
        if not self.mask & other.mask == other.mask:
            return False
        return (self.value & other.mask) == (other.value & other.mask)

    def superset_of(self, other: "Masked") -> bool:
        """Compares with another match, where ``self`` is found to be a superset
        of the other, that is to say; for all :math:`x` in set :math:`B`,
        there exists some element :math:`x` in set :math:`A`.

        A set is a superset of itself.

        Args:

            other (Masked): Other masked value to compare against.

        Returns:

            bool: True if ``self`` is superset of ``other``
        """
        if not self.mask & other.mask == self.mask:
            return False
        return (self.value & self.mask) == (other.value & self.mask)

    def proper_subset_of(self, other: "Masked") -> bool:
        """Compares with another match, where ``self`` is found to be a proper
        subset of the other, that is to say; for all :math:`x` in set :math:`B`,
        there exists some element :math:`x` in set :math:`A`, but there exists
        at least one :math:`x` which exists in set :math:`B` that does not exist
        in set :math:`B`.

        A set is not a proper subset of itself.

        Args:

            Masked:

        Returns:

            bool: True if ``self`` is proper superset of ``other``

        """
        return self.subset_of(other) and not self == other

    def proper_superset_of(self, other: "Masked") -> bool:
        """Compares with another match, where ``self`` is found to be a proper
        superset of the other, that is to say; for all :math:`x` in set
        :math:`A`, there exists some element :math:`x` in set :math:`B`, but
        there exists at least one :math:`x` which exists in set :math:`A` that
        does not exist in set :math:`B`.

        A set is not a proper superset of itself.

        Args:

            Masked:

        Returns:

            bool: True if ``self`` is proper superset of ``other``

        """
        return self.superset_of(other) and not self == other

    def intersection(self, other: "Masked") -> "Masked":
        """Returns the intersection of ``self`` and ``other``.

        The following relations should hold true, noting the use of proper
        subset and superset comparisons:

        .. highlight:: python
        .. code-block:: python

            intersection = a & b
            assert a > intersection
            assert b > intersection

        Since the intersection is the common elements, and if both a and b are
        proper supersets of the intersection, they must contain
        different/unique values.

        Returns:

            Masked: Contains the elements which are common to ``self`` and
            ``other``.
        """
        return self.__class__(
            value=self.value | other.value, mask=self.mask | other.mask
        )

    def union(self, other: "Masked") -> "Masked":
        """
        Returns:

            Masked: Contains all the elements of ``self`` and ``other``
        """
        new_mask = self.mask & other.mask
        return self.__class__(self.value & new_mask, new_mask)

    def overlaps(self, other: "Masked") -> bool:
        """Returns whether or not two ``Masked`` matches overlap.

        Masked expressions can be considered in a context of sets. An
        overlapping set is defined here as where some, but not all, elements in
        a set :math:`A` exist in a set :math:`B`, and, some, but not all,
        elements in :math:`B` exist in :math:`A`. That is to say that they are
        neither proper superset or subset of each other, but they share
        elements.

        If only one of these conditions held true, they would either be a proper
        subset or superset of one another. A corollary to this is that longest
        prefix matches do not overlap, they are strictly a subset or superset of
        one another.

        This can be formalised by the following:

        .. math::

            I = (A \\cap B) \n

        .. math::

            (A \\supsetneq I) {and} (B \\supsetneq I)

        .. drawio-image:: ../drawio/test.drawio
            :align: center


        That is to say that :math:`A`, being a proper superset of the
        intersection :math:`I`, has at least one element not in :math:`I`, and,
        :math:`B`, being a proper superset of :math:`I`, has at least one
        element not in intersection :math:`I`, implying that the elements
        contained in the differences between either :math:`A` or :math:`B`
        and the intersection are unique to each other.

        """
        c_mask = self.mask & other.mask
        return not (c_mask == self.mask or c_mask == other.mask) and (
            self.value & c_mask == other.value & c_mask
        )


    def __hash__(self) -> int:
        """Hashes the value and mask of the match.

        This is useful if the expression is to be used as a key in a dictionary
        like object.

        Args:

            Masked:

        Returns:

            int: Hash of ``self.mask`` and ``self.value``.
        """
        return hash((self.value, self.mask))

    def __le__(self, other: "Masked") -> bool:
        """See :meth:`subset_of`"""
        return self.subset_of(other)

    def __ge__(self, other: "Masked") -> bool:
        """See :meth:`superset_of`"""
        return self.superset_of(other)

    def __lt__(self, other: "Masked") -> bool:
        """See :meth:`proper_subset_of`"""
        return self.proper_subset_of(other)

    def __gt__(self, other: "Masked") -> bool:
        """See :meth:`proper_superset_of`"""
        return self.proper_superset_of(other)

    def __eq__(self, other: "Masked") -> bool:
        return (self.value == other.value) & (self.mask == other.mask)

    def __and__(self, other: "Masked") -> "Masked":
        """Returns the intersection of ``self`` and ``other``.

        see :meth:`intersection`

        """
        return self.intersection(other)

    def __or__(self, other: "Masked") -> "Masked":
        return self.union(other)

    def __iter__(self) -> "Masked.__iter__.iterator":
        """Creates an `iterator` that returns consecutive elements in the set of
        ``Masked``, starting from the current value.

        Examples:

            Using a ``PortID``:

                >>> match = Ternary(PortId(0x0), mask=0xc)
                >>> [str(x) for x in iter(match)]
                [
                    '0x0 &&& 0xf3',
                    '0x4 &&& 0xf3',
                    '0x8 &&& 0xf3',
                    '0xc &&& 0xf3'
                ]

            Or an ``IPv4Address``:

                >>> match = Ternary(IPv4Address("192.168.42.24"),
                ..      mask="255.255.255.252")
                >>> [str()]
                [
                    '192.168.42.24 &&& 255.255.255.252',
                    '192.168.42.25 &&& 255.255.255.252',
                    '192.168.42.26 &&& 255.255.255.252',
                    '192.168.42.27 &&& 255.255.255.252',
                ]
        """

        def iterator(ternary):
            global_max_value = (1 << self.value.bitwidth) - 1
            local_max_val = global_max_value - self.mask.value
            local_max_val = self.value.value | local_max_val
            temp = self.value.value

            match_cls = self.__class__
            value_cls = self.value.__class__
            yield match_cls(value_cls(temp), value_cls(global_max_value))

            initial = self.value.value
            mask = self.mask.value
            while temp < local_max_val:
                temp += 1
                if temp & mask != initial:
                    continue
                if temp & initial != temp:
                    yield match_cls(value_cls(temp),
                                    value_cls(global_max_value))

        return iterator(self)


class Ternary(Masked):
    """Matches values on specific bits.

    A ``Ternary`` match is a match type which matches on specific bits of the
    value. This is achieved by the use of a mask; when a match is performed,
    both the the expected value and the compared value are ANDed with the mask,
    and an equality operation can be performed without comparing every single
    bit.

    ``Ternary`` values are associated with TCAM () memory; and are stored in
    hardware as `trits`. These are like bits but have 3 states, on, off, and
    "don't care".

    Note:
        Masks could be represented by either ``0`` or ``1`` for a match. In
        this case, ``1`` bits represent bit's which are matched against.

    This class represents a ternary expression as a combination of an integer
    value and a mask. This is because:

    * Python supports arbitrary length integers;
    * It is easier to perform bitwise operations on integers.

    Args:
        value (Field): The instance of a field, e.g. ``VlanID()``,
                ``MACAddress()``, etc.
        mask (Field): The mask representing the bits to match against, either as
                an instance of the value's type, or, a value that can be passed
                to that type's constructor.
        dont_care (bool): If ``True``, no bits will be considered.

    The semantics of this match can change depending on whether a mask or
    ``dont_care`` is specified. By default, creating a ``Ternary`` match
    without a ``mask`` will match on every single bit, effectively acting in the
    same way as :class:`bfrt_helper.match.Exact`.

    The mask value does not have to be specified explictly as the same type as
    the value, any value will be accepted so long as it would be accepted by
    the value types constructor.

    If ``dont_care`` is specified, no bits will be compared (i.e, the mask will
    contain all zeroes). This means that it will match on any value it's
    compared against. This can be useful if a `table` specifies multiple key
    fields, and you wanted to match on another field, but not this specific
    ``Ternary`` element.

    Examples:
        A match on a ``PortId`` which only considers the 4 least significant
        bits::

            my_field = Ternary(PortId(42), PortId(0xf))

        A match on a ``PortId`` which only considers the 4 least significant
        bits, but not specifying the mask in terms of the original type::

            my_field = Ternary(PortId(42), 0xf)

        A match that will match exactly on a ``PortId`` of 42::

            my_field = Ternary(PortId(42))

        A match that will match on any other ``PortId``::

            my_field = Ternary(PortId(42), dont_care=True)


    """

    def __init__(self, value: Field, mask: Field = None, dont_care=False):
        super().__init__()

        self.max_value = (2 ** value.bitwidth) - 1
        self.value = value
        self.mask = mask

        if mask is None:
            required_bytes = (value.bitwidth + 7) // 8
            if dont_care:
                mask_int = 0
                mask_bytes = mask_int.to_bytes(required_bytes, "big")
                mask = value.__class__.from_bytes(mask_bytes)
            else:
                mask_int = (1 << value.bitwidth) - 1
                mask_bytes = mask_int.to_bytes(required_bytes, "big")
                mask = value.__class__.from_bytes(mask_bytes)
        elif not isinstance(mask, value.__class__):
            mask = value.__class__(mask)

        self.value = value & mask
        self.mask = mask

    def value_bytes(self):
        """Returns the match value as bytes.

        Returns:
            bytes: Internal value converted into bytes.
        """
        return self.value.to_bytes()

    def mask_bytes(self):
        """Returns the mask value as bytes.

        Returns:
            bytes: Internal mask converted into bytes.
        """
        return self.mask.to_bytes()

    @classmethod
    def dont_care(self):
        """Not implemented"""
        pass

    def __str__(self):
        """Returns a string representation of the match.

        The string representation is output in terms of how this would be
        written in a P4 program. A value in P4 which is two numbers separated
        by a triple ampersand (in the correct context) is a ternary expression.

        Example:

            >>> match = Ternary(PortId(0x42), 0x0f)
            >>> str(match)
            0x42 &&& 0xf

        Returns:

            str: String representation of the match in terms of how it would be
            written in P4.

        """
        if self.mask.value == self.max_value:
            return str(self.value)
        return f"{str(self.value)} &&& {str(self.mask)}"

    def __repr__(self):
        return f"Ternary({repr(self.value)}, mask={repr(self.mask)})"


class LongestPrefixMatch(Masked):
    def __init__(self, value: Field, prefix: int):
        super().__init__()

        if prefix > value.bitwidth:
            msg = f"Prefix {prefix} is greater than the maximum allowed for "
            msg += f"this field. [bitwidth={value.bitwidth}]"
            raise InvalidValue(msg)
        self.mask = value.__class__((2 ** prefix - 1) << (value.bitwidth -
                                                          prefix))
        self.value = value & self.mask
        self.prefix = prefix

    def __str__(self):
        return f"{self.value}/{self.prefix}"

    def __repr__(self):
        return f"LongestPrefixMatch({repr(self.value)}, prefix={self.prefix})"

    def value_bytes(self):
        return self.value.to_bytes()


class Exact:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def value_bytes(self):
        return self.value.to_bytes()


class Match:
    """A collection of fields representing the key segment of a table defined in
    a P4 program.
    """

    def __init__(self, **fields):
        self.fields = fields

    def __gt__(self, other):
        """See :meth:`proper_superset_of`"""
        return self.proper_superset_of(other) and not self == other

    def __lt__(self, other):
        """See :meth:`proper_subset_of`"""
        return self.proper_subset_of(other) and not self == other

    def __ge__(self, other):
        """See :meth:`superset_of`"""
        return self.superset_of(other)

    def __le__(self, other):
        """See :meth:`subset_of`"""
        return self.subset_of(other)

    def __eq__(self, other):
        return self.equal_(other)

    def __hash__(self):
        return hash((*self.fields.keys(), *self.fields.values()))

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def __equality_check(self, other):
        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if k1 != k2:
                raise MismatchedKeys(f"Key {k1} is not equal to {k2}")
            if type(v1) != type(v2):
                raise MismatchedTypes(
                    (f"Type of {v1} ({type(v1)}) is not equal to {v2} ",
                     f"({type(v2)})")
                )

    def conflicts(self, other):

        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1.conflicts(v2)
            else:
                acc = acc and v1 == v2
        return acc

    def intersection(self, other):
        """Calculates the intersection of values between two matches.

        Raises:
            MismatchedKeys:
                Raised if a key does not match it's respective compared match.
                Implies that match fields must be ordered correctly.
        """
        args = {}

        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if isinstance(v1, Ternary):
                # args.append(v1.intersection(v2))
                args[k1] = v1.intersection(v2)
            elif isinstance(v1, LongestPrefixMatch):
                # args.append(LongestPrefixMatch(v1.value | v2.value, max(v1.prefix,
                #   v2.prefix)))
                args[k1] = LongestPrefixMatch(v1.value | v2.value, max(v1.prefix, v2.prefix))
            else:
                if v1 != v2:
                    raise InvalidOperation(
                        "Trying to calculate the difference "
                        + "on matches containing non-equal exact values."
                    )
                args[k1] = v1
        return Match(**args)

    def superset_of(self, other):
        """Calculates whether one match is a superset of another

        For this to hold true, all fields must be superset of their compared
        respective fields.

        See :meth:`Masked.superset_of`.

        Raises:
            MismatchedKeys:
                Raised if a key does not match it's respective compared match.
                Implies that match fields must be ordered correctly.
        """
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 >= v2
            else:
                acc = acc and v1 == v2
        return acc

    def subset_of(self, other):
        """Calculates whether one match is a superset of another

        For this to hold _true,_ all fields must be subset of their compared
        respective fields.

        See :meth:`Masked.subset_of`.

        Raises:
            MismatchedKeys:
                Raised if a key does not match it's respective compared match.
                Implies that match fields must be ordered correctly.
        """
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 <= v2
            else:
                acc = acc and v1 == v2
        return acc

    def proper_superset_of(self, other):
        """Calculates whether one match is a proper superset of another

        For this to hold true, all fields must be proper superset of their
        compared respective fields.

        See :meth:`Masked.proper_superset_of`.

        Raises:
            MismatchedKeys:
                Raised if a key does not match it's respective compared match.
                Implies that match fields must be ordered correctly.
        """
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 > v2
            else:
                acc = acc and v1 == v2
        return acc

    def proper_subset_of(self, other):
        """Calculates whether one match is a proper superset of another

        For this to hold true, all fields must be proper superset of their
        compared respective fields.

        See :meth:`Masked.subset_of`.

        Raises:
            MismatchedKeys:
                Raised if a key does not match it's respective compared match.
                Implies that match fields must be ordered correctly.
        """
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 < v2
            else:
                acc = acc and v1 == v2
        return acc
        # return acc

    def equal_(self, other):
        """Calculates whether two matches are equal.

        For this to hold true, every single element must equal it's other.

        Raises:
            MismatchedKeys:
                Raised if a key does not match it's respective compared match.
                Implies that match fields must be ordered correctly.
        """
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            acc = acc and v1 == v2
        return acc

    def overlaps(self, other):
        acc = True

        if self <= other:
            return False
        if self >= other:
            return False
        if self == other:
            return False

        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(self.fields.items(),
                                      other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and (v1 >= v2 or v1 <= v2 or v1.overlaps(v2))
            else:
                acc = acc and v1 == v2
        return acc

    def __str__(self):
        field_strings = []
        for k, v in self.fields.items():
            if isinstance(v, Ternary):
                if v.mask.value == 0:
                    field_strings.append("_")
                else:
                    field_strings.append(str(v))
            else:
                field_strings.append(str(v))
        return "{{  {}  }}".format(", ".join(field_strings))

    def __repr__(self):
        acc = "Match("
        acc += ", ".join([f'"{k}={repr(v)}"' for k, v in self.fields.items()])
        return acc + ")"


class IPv4AddressTernary(Ternary):
    """A helper class for more easily expressing a ternary ``IPv4Address``."""

    def __init__(self, value, *, prefix=None, mask=None, dont_care=False):
        if not isinstance(value, IPv4Address):
            value = IPv4Address(value)
        if prefix:
            mask = IPv4Address(mask_from_prefix(IPv4Address.bitwidth, prefix))

        super().__init__(value, mask, dont_care)

    # def __str__(self):
    #     print('IPv4AddressTernary.__str__')
    #     if self.mask.value == self.max_value:
    #         return str(self.value)
    #     return f"{str(self.value)} &&& {str(self.mask)}"

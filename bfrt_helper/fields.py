#!/usr/bin/env python
# -*- coding: utf-8 -*-


import ipaddress

from enum import Enum
from bfrt_helper.util import InvalidValue
from bfrt_helper.util import InvalidOperation
from bfrt_helper.util import encode_number


class MismatchedTypes(Exception):
    """Raised when a field's type (e.g., bitwidth or object) do not match when
    comparing two match objects.
    """

    def __init__(self, a, b):
        super().__init__(
            f"Type {a.__class__.__qualname__} is not {a.__class__.__qualname__}"
        )


class JSONSerialisable:
    """Base class that enables converting a derived's contents to JSON"""

    def json(self):
        """Generates a dictionary representation of a classes contents."""
        result = {}
        for key, value in self.__dict__.items():
            result[key] = JSONSerialisable.serialise(value)
        return result

    @staticmethod
    def serialise(value):
        """Recursively descends, serialising class members"""
        if isinstance(value, list):
            return [JSONSerialisable.serialise(x) for x in value]
        elif isinstance(value, dict):
            return {k: JSONSerialisable.serialise(v) for k, v in value.items()}
        elif isinstance(value, Field):
            return value.value
        elif isinstance(value, JSONSerialisable):
            return value.json()
        elif isinstance(value, Enum):
            return value.name
        else:
            return value


def type_check(a, b):
    if type(a) != type(b):
        raise MismatchedTypes(a, b)


class Field(JSONSerialisable):
    """Base class for all BfRt Helper field objects.

    A field is datatype and value defined within a P4 program. Such fields can
    be manipulated using gRPC, however requires translation from the client side
    as types can have arbitrary bitwidths.

    Internally, the value is stored as an integer, since bitwise operations are
    easier to apply.

    Raises:
        InvalidValue:
            Raised if the value assigned to the object is greater than the
            maximum permissable value
    """

    def __init__(self, value=0):

        if hasattr(self, "bitwidth"):
            max_value = self.__class__.max_value()
            if value > max_value:
                msg = f"Value {value} is greater than the maximum allowed for "
                msg += "this "
                msg += f" field. [max={max_value}, bitwidth={self.bitwidth}]"
                raise InvalidValue(msg)
        self.value = value

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        if hasattr(cls, "bitwidth"):
            instance.bitwidth = cls.bitwidth
        return instance

    def to_bytes(self):
        """Converts internal value to a byte array representing the contents

        When marshalling to gRPC, the byte representation is used.
        """
        return encode_number(self.value, self.bitwidth)

    @classmethod
    def from_bytes(cls, data):
        """Accepts a string of bytes and converts it to an instance of the
        derived class.
        """
        return cls(int.from_bytes(data, "big"))

    @classmethod
    def max_value(cls):
        """Using the derived classes bitwidth, retrieve the maximum value. This
        is :math:`2^x-1`.
        """
        return 2**cls.bitwidth - 1

    def __str__(self):
        if isinstance(self.value, str):
            return f"'{self.value}'"
        return str(self.value)

    def __repr__(self):
        return f"{self.__class__.__qualname__}({str(self)})"

    def __eq__(self, other):
        type_check(self, other)
        if self.__class__ != other.__class__:
            return False
        return self.value == other.value

    def __and__(self, other):
        type_check(self, other)
        cls = self.__class__
        return cls(self.value & other.value)

    def __or__(self, other):
        type_check(self, other)
        cls = self.__class__
        return cls(self.value | other.value)

    def __xor__(self, other):
        type_check(self, other)
        cls = self.__class__
        return cls(self.value ^ other.value)

    def __hash__(self):
        return hash(self.value)

    def __ne__(self, other):
        type_check(self, other)
        return self.value != other.value

    def __le__(self, other):
        type_check(self, other)
        return self.value <= other.value

    def __lt__(self, other):
        type_check(self, other)
        return self.value < other.value

    def __ge__(self, other):
        type_check(self, other)
        return self.value >= other.value

    def __gt__(self, other):
        type_check(self, other)
        return self.value > other.value


""" For data parameters, this may not even be necessary as the class will accept
    a string directly"""


class StringField(Field):
    """Represents a gRPC string field.

    Note:
        This is here for completeness purposes only, and is not used (perhaps
        even required), by any available gRPC function (so far).
    """

    def __and__(self, other):
        raise InvalidOperation("StringField.__and__ not allowed")

    def __or__(self, other):
        raise InvalidOperation("StringField.__or__ not allowed")

    def __xor__(self, other):
        raise InvalidOperation("StringField.__xor__ not allowed")

    def max_value(cls):
        raise InvalidOperation("StringField.max_value not allowed")

    def to_bytes(self):
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, data):
        raise NotImplementedError()


class IPv4Address(Field):
    """Utility class for better representing IP addresses in a more pleasing
    way.

    Can accept string representations and internally convert them to
    the required integer type, and vice versa when printing as a string. When
    the value is sent to the gRPC interface, it will be converted to a byte
    array as required.

    Uses the ``ipaddress`` module.

    Args:
        address (str): Dotted decimal IPv4 address string
    """

    bitwidth = 32

    def __init__(self, address: str):
        super().__init__(int(ipaddress.ip_address(address)))

    def __str__(self):
        return str(ipaddress.ip_address(self.value))

    """ Overloaded cause of quotes"""

    def __repr__(self):
        return f"IPv4Address('{str(self)}')"

    @classmethod
    def from_bytes(cls, data):
        return cls(ipaddress.ip_address(data).__str__())


class MACAddress(Field):
    """Utility class for better representing IP addresses in a more pleasing
    way.

    Can accept string representations and internally convert them to
    the required integer type, and vice versa when printing as a string. When
    the value is sent to the gRPC interface, it will be converted to a byte
    array as required.

    Internally uses string manipulation and integer casting for serialisation
    from and to integer value.

    Args:
        address (str): Colon seperated 6 byte hexadecimal address string.
    """

    bitwidth = 48

    def __init__(self, address):
        if isinstance(address, int):
            super().__init__(address)
        else:
            super().__init__(int(address.replace(":", ""), 16))

    def __str__(self):
        return ":".join([f"{b:02x}" for b in self.value.to_bytes(6, 16)])

    # def __repr__(self):
    #     return f'MACAddress(\'{str(self)}\')'

    @classmethod
    def from_bytes(cls, data):
        return cls(":".join([f"{b:02x}" for b in data.to_bytes(6, 16)]))


class PortId(Field):
    """Typical port id data type.

    The port id typically represents an egress or ingress port, and is 9 bits
    wide.

    Args:
        value (int): Port id.
    """

    bitwidth = 9


class MulticastGroupId(Field):
    """Mutlicast group P4 data type, as defined by the Tofino core architecture

    Args:
        value (int): Group id.
    """

    bitwidth = 16


class MulticastNodeId(Field):
    bitwidth = 32


class DevPort(Field):
    bitwidth = 32


class VlanID(Field):
    """User class representing a parsed Vlan ID

    Args:
        value (int): VLAN id.
    """

    bitwidth = 12


class EgressSpec(Field):
    """Legacy port representation"""

    bitwidth = 9


class DigestType(Field):
    """Representation of a digest as defined in the BfRt spec.

    A digest is used to send messages from the Tofino hardware to the runtime
    components. The 3 bit field can be used to inform the controller of any
    special semantics for a given message, for instance what type it is, or
    what data it includes. For instance, you could send a message containing
    an IP address, but change the digest type depending on whether it was
    IPv4 or IPv6.

    Another example would be notifying the controller of any new MAC addresses
    seen on the wire.

    In any case, this would not typically be used to send messages, but instead
    is useful for storing when received.
    """

    bitwidth = 3


class ReplicationId(Field):
    """Representation of a replication ID as defined in the BfRt spec

    A replication id is a tag that is added to metadata that can be used to
    perform additional operations when moving packets across multicast groups.
    """

    bitwidth = 16


class Layer2Port(Field):
    bitwidth = 16

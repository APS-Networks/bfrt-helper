Fields
------

In P4 parlance, a field is typically an integer constrained by a bit width, and
is either a member of a key field for a "match table", or a value passed as an
action parameter when a key field is matched.

In order to present a field value to any element mentioned previously, you would
first have to construct a gRPC field object, and then serialise an integer value
into a byte array. I would argue that this is *inconvenient* to do, and that
they can be presented in a far more obvious and human readable way.

This library provides a ``Field`` object that can be derived from to define
data types constrained by a bit width, checking whether a value used to
construct an instance is representable by this constraint, and lends itself to
type checks further down the line.

An example in this library is the :ref:`Layer2Port` field. It represents a 
source or destination port in a layer 3 protocol such is ICMP, TCP or UDP.

.. code:: python

    from bfrt_helper.fields import Layer2Port

    port = Layer2Port(80)


And this is defined simply as:

.. code:: python

    from bfrt_helper.fields import Field

    class Layer2Port(Field):
        bitwidth = 16

The only thing required is that the bit width is specified. Python magic does
all the rest.

Existing Fields
^^^^^^^^^^^^^^^

The following fields are defined already:

* :ref:`DevPort`
* :ref:`DigestType`
* :ref:`EgressSpec`
* :ref:`IPv4Address`
* :ref:`Layer2Port`
* :ref:`MACAddress`
* :ref:`MulticastGroupId`
* :ref:`MulticastNodeId`
* :ref:`PortId`
* :ref:`ReplicationId`
* :ref:`StringField`
* :ref:`VlanID`


Defining Custom Fields
^^^^^^^^^^^^^^^^^^^^^^

If fields are represented by a simple integer value, then they can be defined
as in the previous example. However, some fields have more **interesting**
expressions, such as an :ref:`IPv4Address` or :ref:`MACAddress`. In this case
you will need to overload the constructor, the deserialisation method
``from_bytes``, and optionally the ``__str__`` method.

An example of this is indeed an :ref:`IPv4Address`:

.. code:: python

    class IPv4Address(Field):
        bitwidth = 32

        def __init__(self, address: str):
            super().__init__(int(ipaddress.ip_address(address)))

        def __str__(self):
            return str(ipaddress.ip_address(self.value))

        @classmethod
        def from_bytes(cls, data):
            return cls(ipaddress.ip_address(data).__str__())

The constructor is overloaded as the underlying value type is required to be an
integer, so we use the ``ipaddress`` Python library to convert a human readable
address into a number.

The reason for overloading the ``__str__`` method should be obvious; when it is
printed you will again have nice readable expression.

Finally, the ``from_bytes`` function is required to deserialise data from the
device.

Another example is :ref:`MACAddress`:


.. code:: python

    class MACAddress(Field):
        bitwidth = 48

        def __init__(self, address):
            if isinstance(address, int):
                super().__init__(address)
            else:
                super().__init__(int(address.replace(":", ""), 16))

        def __str__(self):
            return ":".join([f"{b:02x}" for b in self.value.to_bytes(6, 16)])

        @classmethod
        def from_bytes(cls, data):
            return cls(":".join([f"{b:02x}" for b in data.to_bytes(6, 16)]))

For some reason I decided to allow the address to be supplied as in integer.
I can't for the life of me remember why.


Operations on Fields
^^^^^^^^^^^^^^^^^^^^

Fields have convenience operators defined for comparisons. The 
operators available are:

* ``==`` (equality)
* ``!=`` (inequality)
* ``&`` (bitwise *AND*)
* ``|`` (bitwise *OR*)
* ``^`` (bitwise *XOR*)
* ``<=`` (less than or equal to)
* ``<`` (less than)
* ``>=`` (greater than or equal to)
* ``>`` (greater than)

Additionally, a hash is available via ``hash(field)`` (``__hash__``).

The use cases for most are straightforward, however an interesting case is
perform masking operations such as on an :ref:`IPv4Address`:

.. code:: python

    from bfrt_helper.fields import IPv4Address

    addr = IPv4Address('192.168.0.46')
    mask = IPv4Address('255.255.255.0')

    masked = addr & mask
    expected = IPv4Address('192.168.0.0')

    assert masked == expected
    assert str(masked) == '192.168.0.0'

Yes, this could be done with native libraries such as the 
`ipaddress module <https://docs.python.org/3/library/ipaddress.html>`_, but
again this is to provide similar operations natively. 


More of these operators can be added, with reference to the
`Python data model <https://docs.python.org/3/reference/datamodel.html>`_.

.. note::

    Currently, any comparison operator performs a strict test against their
    types. However, such operators could reasonably expected to work against
    fields with the same bit width. The view is that the current position is
    sensible, but we are open to changing this. It is almost certainly better to
    start more strict, as any code which would rely on the alternative semantics
    would surely fail on a change.

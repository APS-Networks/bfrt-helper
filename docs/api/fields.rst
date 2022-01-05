bfrt_helper.fields
------------------

.. 
   inserts local table of contents

.. contents:: :local:
   :depth: 3

.. currentmodule:: bfrt_helper.fields

..
   Unfortunately we need to specify each class individually, as running
   automodule doesn't provide toctree elements for each class. What we want is
   to have each class visible in the left hand navigation.

Base Fields
^^^^^^^^^^^

JSONSerialisable
****************
.. autoclass:: JSONSerialisable
   :members:

Field
*****
.. autoclass:: Field
   :members:



Predefined Fields
^^^^^^^^^^^^^^^^^

DevPort
*******
.. autoclass:: DevPort
   :members: bitwidth

DigestType
**********
.. autoclass:: DigestType
   :members: bitwidth

EgressSpec
**********
.. autoclass:: EgressSpec
   :members: bitwidth

IPv4Address
***********
.. autoclass:: IPv4Address
   :members: bitwidth

Layer2Port
**********
.. autoclass:: Layer2Port
   :members: bitwidth

MACAddress
**********
.. autoclass:: MACAddress
   :members: bitwidth

MulticastGroupId
****************
.. autoclass:: MulticastGroupId
   :members: bitwidth

MulticastNodeId
***************
.. autoclass:: MulticastNodeId
   :members: bitwidth

PortId
******
.. autoclass:: PortId
   :members: bitwidth

ReplicationId
*************
.. autoclass:: ReplicationId
   :members: bitwidth

StringField
***********
.. autoclass:: StringField
   :members: bitwidth

VlanID
******
.. autoclass:: VlanID
   :members: bitwidth


Exceptions
^^^^^^^^^^

MismatchedKeys
**************
.. autoclass:: MismatchedTypes


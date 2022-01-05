Overview
--------

The motivation for this is as follows:

* It provides useful examples for interacting with such an interface;
* It can be used in a self-contained Python virtual environment, without any
  dependency on an installed SDE, and as such can be used remotely. It does
  however require the protobuf definition.
* While the SDE does come packaged with it's own client, there is little in the
  way of documentation, and it's not obvious how this is installed.


There are four main components to the library:

* The ``BfRtInfo`` object which is responsible for parsing the ``bfrt.json``
  information file. This is not generally intended for direct use. After all,
  it is essentially a transformation of a JSON document.
* The ``BfRtHelper`` which creates gRPC requests;
* The collection of ``Field`` objects which represents the data types that can
  be sent to a device;
* And finally the ``Match`` objects which represents that combination of fields
  and match types that can be supplied to a P4 table.



Usage
^^^^^

Taking a hypothetical program called `port_forward` which directs packets based
on the input port to an output port, we can create the appropriate request with
the following example:

.. code-block:: python

    DEVICE_ID = 0
    CLIENT_ID = 0
    INGRESS_PORT = 0
    EGRESS_PORT = 64

    bfrt_data = json.loads(open("bfrt.json").read())
    bfrt_info = BfRtInfo(bfrt_data)
    bfrt_helper = BfRtHelper(DEVICE_ID, CLIENT_ID, bfrt_info)

    write_request = bfrt_helper.create_table_write( 
        program_name='forwarder', 
        table_name='pipe.PortForward.destination_port',
        key={
            'ig_intr_md.ingress_port': Exact(PortId(INGRESS_PORT))
        },
        action_name='PortForward.forward',
        action_params={
            'egress_port': PortId(EGRESS_PORT),
        })  

.. pull-quote::

    ``ig_intr_md`` is an argument passed to the ingress controller by the 
    Tofino model; it is a shortening of "ingress intrinsic metadata", and
    funnily enough, contains metadata specific to the ingress. The name it's
    given is one that is found throughout Intel's P4 examples. If you were to
    declare it with a different name, you would have to update it here.

Running through the code, we open our BfRt file, and construct a ``BfRtInfo``
object with it, using it to construct the helper object along with the 
device and client ID.

You should be able to see that this is completely independent of any kind
of gRPC client. This may be useful if you want to verify bf runtime gRPC
objects without having to connect to a device (and consequently manage
the stream channel, messages across the device, subscription requests etc).


Building
^^^^^^^^


Installing
^^^^^^^^^^


Building/Running Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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


.. note::

    * This documentation is incomplete. If you have any questions or would like
      to see something added, please contact :email:`support@aps-networks.com`.
    * Please note that at this time we are unable to accept pull requests as
      APS Networks is reserving the right to dual licence this library. Any
      contributions would therefore have to be issued with a rights assignment.


Requirements
^^^^^^^^^^^^

The requirements should be handled by the pip install process. However, Python 3
is required.

Installing
^^^^^^^^^^

1. Copy the BfRt Protobuf definition into ``proto/bfrt_helper/pb2``.
2. From the root of the project, run ``pip install``.

Usage
^^^^^

.. toctree::
   :maxdepth: 1

   fields
   match


Basic Example
*************

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


Retrieving Non-P4 Configuration
*******************************

It is possible to retrieve from the device non-P4 tables, which can be merged
with the runtime configuration to provide a more complete view of the state of
a device.

.. code:: 

    request = bfrt_helper.create_get_pipeline_request()
    response = client.GetForwardingPipelineConfig(request)

    program_name = response.config[0].p4_name
    data = response.non_p4_config.bfruntime_info.decode("utf-8")
    non_p4_config = json.loads(data)

    p4_config = None

    for config in response.config:
        if program_name == config.p4_name:
            p4_config = json.loads(config.bfruntime_info)
            p4_config.get("tables").extend(non_p4_config.get("tables"))

    with open('all.json', 'w') as fd:
        fd.write(json.dumps(p4_config, indent=2))



Manipulating Non-Match/Action Tables
************************************

As mentioned previously, some non-P4 tables can be retrieved from the device.
For a subset of these, it is also possible to manipulate them. These can be used
to add/alter copy to cpu settings, multicast groups, port settings etc.

While these tables can be considered as "ordinary" database tables, they are
still manipulated by the same mechanisms as a match-action update.

While this is not guaranteed to work (or indeed supported by Intel), what
follows is an example of creating a request to add a ``copy_to_cpu``
configuration:


.. code:: python

  # Assuming bfrt_helper et. al. have been created prior

    port = 64

    bfrt_request = helper.create_write_request(program_name)
    bfrt_table_entry = helper.create_table_entry("$pre.port")

    # The first argument is the table name, the second the field to write, and
    # the final is the value to lookup
    #                                         table        key name    key value     
    bfrt_key_field = helper.create_key_field("$pre.port", "$DEV_PORT", Exact(port))
    bfrt_table_entry.extend([bfrt_key_field])

    info_cpu_port_field = self.bfrt_info.get_data_field(
    #   table         field
        "$pre.port", "$COPY_TO_CPU_PORT_ENABLE"
    )

    bfrt_cpu_port_field = self.create_data_field(
        info_cpu_port_field.singleton, True
    )
    bfrt_table_entry.data.fields.extend([bfrt_cpu_port_field])

    bfrt_update = bfrt_request.updates.add()
    bfrt_update.type = bfruntime_pb2.Update.Type.MODIFY
    bfrt_update.entity.table_entry.CopyFrom(bfrt_table_entry)


For information on tables that may be modifiable, look at the non-P4 config for
fields which have the ``"read_only": true`` attribute.

.. warning::

  You modify other tables at your peril. The extent to which you can alter the
  behaviour of the device is not well understood. It may be possible to 
  cause the ASIC to function incorrectly.



Building Documentation
^^^^^^^^^^^^^^^^^^^^^^

The documentation is built in a Python virtual environment using
`Sphinx <https://www.sphinx-doc.org/en/master/>`_ and can be done with a handy
1-liner:

.. code:: bash

    ./scripts/build-docs.sh && (cd docs/_build/html && python3 -m http.server)
Barefoot Runtime gRPC Helper
============================

``bfrt-helper`` is a library for creating gRPC messages and communicating with
devices exposing a Barefoot Runtime gRPC interface. 

.. note::

    .. rubric:: Disclaimer
    1. This is not a substitute for Intel's documentation and that in the event
       of any discrepancies, you should refer to their documentation.
    2. The building of this library requires a copy of the Intel Barefoot
       Runtime gRPC Protocol Buffers definition, which is included as a part of
       the Barefoot SDE. This is available under license from Intel and requires
       the signing of a non-disclosure agreement. We are not able to supply
       this.
    3. As a consequence of *2*, we are unable to discuss Tofino specific
       specifications, technical data, workarounds, and other errata.  

.. code-block:: python

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


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   fields
   match
   examples
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

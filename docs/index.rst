Barefoot Runtime gRPC Helper
============================

``bfrt-helper`` is a library for creating gRPC messages and communicating with
devices exposing a Barefoot Runtime gRPC interface. 

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

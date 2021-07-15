# Barefoot Runtime Helper

This library is a helper for creating gRPC messages for devices accepting a
Barefoot Runtime gRPC interface. It does not concern itself with details of the
connection or how messages are handled; that is an exercise for the reader.

* `bfrt_info.py`: Utility classes for reading Barefoot Runtime information
    files. It does not depend on any protobuf code, it is merely limited to
    parsing the information document to retrieve information on specific
    elements, as well as resource identifiers.
* `bfrt.py`: Utility class for constructing BfRt gRPC requests. The existence of
    class (rather than straight functions) is to wrap the device and client ID's
    which are by far the most commonly used variables that are common to any
    request to a specific device.
* `fields.py`: Set of helper classes that define P4 objects. They allow:
    * Runtime checking of match types against `Exact`, `Ternary` and `LPM`;
    * Runtime checking of the bit widths of fields, either match or action

  Some common fields have been defined for you:, e.g.
    * `VlanID` (bit width of 9)
    * `PortId` (bit width of 9)
    * `DevPort` (bit width of 32)
    * `MacAddress` (bit width of 48, with custom serialisation)
    * `IPv4Address` (bit width of 32, with custom serialisation)


## Usage

The following example creates a gRPC request to add a rule to a table.

This theoretical program forwards ports from one device port to another.


```python
DEVICE_ID = 0
CLIENT_ID = 0

bfrt_data = json.loads(open("bfrt.json").read())
bfrt_info = BfRtInfo(bfrt_data)
bfrt_helper = BfRtHelper(DEVICE_ID, CLIENT_ID, bfrt_info)

write_request = bfrt_helper.create_table_write( 
    program_name='forwarder', 
    table_name='pipe.PortForward.destination_port',
    key={
        'ig_intr_md.ingress_port': Exact(PortId(0))
    },
    action_name='PortForward.forward',
    action_params={
        'egress_port': PortId(64),
    })
```

> `ig_intr_md` is an argument passed to the ingress controller; it is
> a shortening of "ingress intrinsic metadata", and funnily enough, 
> contains metadata specific to the ingress. The name it's given is one
> that is found throughout Intel's P4 examples. If you were to declare it
> with a different name, you would have to update it here.

Running through the code, we open our BfRt file, and construct a `BfRtInfo` 
object with it, using it to construct the helper object along with the 
device and client ID.

You should be able to see that this is completely independent of any kind
of gRPC client. This may be useful if you want to verify bf runtime gRPC
objects without having to connect to a device (and consequently manage
the stream channel, messages across the device, subscription requests etc).

Other functions available are:
* `create_subscribe_request`
* `create_write_request`
* `create_table_entry`
* `create_key_field`
* `create_data_field`
* `create_key_fields`
* `create_action`
* `create_table_write`
* `create_copy_to_cpu` (I'm pretty sure this is a hack)
* `create_set_pipeline_request`
* `create_get_pipeline_request`



## Acknowledgements

This library makes use of code from and is inspired by
[Simple P4 Client](https://github.com/CommitThis/simplep4client).

This in turn is inspired by code from [P4 Tutorial](https://github.com/p4lang/tutorials)

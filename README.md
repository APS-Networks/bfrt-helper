# Barefoot Runtime Helper

REQUIRES SANITATION BEFORE RELEASE

> This documentation is for the APS Networks `bfrt-helper` software. The source
> code for this is available on GitHub.
>
> [bfrt-helper](https://github.com/APS-Networks/bfrt-helper) on GitHub

`bfrt_helper` is a library for creating gRPC messages and communicating with
devices exposing a Barefoot Runtime gRPC interface. The motivation for this is
as follows:

* It provides useful examples for interacting with such an interface;
* It can be used in a self-contained Python virtual environment, without any
  dependency on an installed SDE, and as such can be used remotely. It does
  however require the protobuf definition for the interface.
* While the SDE does come packaged with it's own client, there is little in the
  way of documentation, and it's not obvious how this is installed.

> The protobuf definition, as of writing, is Intel proprietary and confidential,
> and therefore cannot be shared. Otherwise this would be provided.

## Overview

The library comes supplied with the following python files:

* `bfrt_info.py`: This is a utility class for parsing Barefoot Runtime
  information files. This is not dependent on any external code, it merely
  parses the Barefoot jSON documented created when a program is compiled.
* `bfrt.py`: This is a utility class for constructing BfRt gRPC requests. This
  could have been written as a collection of standalone methods, however to
  make things easy it encapsulates both a `DEVICE_ID` and `CLIENT_ID`, the most
  common variables used when communicating with a device, which are required in
  every(?) single request.
* `fields.py`: These define classes that represent objects sent with a request,
  what kind of match it is for a key field, and handle serialisation and
  deserialisation of such.

## Usage

Taking a hypothetical program called `port_forward` which directs packets based
on the input port to an output port, we can create the appropriate request with
the following example:

```python
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

## Fields

In this library, a field is either an element of a key for a table rule, or a
parameter to any action defined in such.

With a few exceptions, values sent to a device should be serialised into a byte
array with a size of the smallest number of bytes required to fit. However,
it is often inconvenient to write code that does this, and in a lot of cases
would be far more useful to be represented to the user in a human readable way.

Two fields which demonstrate this are an `IPv4Address` and a `MacAddress`,
which are most often represented as octet strings. In the case of an IP version
4 address, this is decimal octets, delimited by a full stop (e.g. 
`192.168.0.1`), and in the case of a MAC address, this is hexadecimal octets
which are colon delimited (e.g `11:22:33:aa:bb:cc`).

Both the `IPv4Address` and `MacAddress` classes enables a user to write the
fields in a human readable way:

```python
ip_addr = IPv4Address("192.168.0.1")
mac_addr = MacAddress("11:22:33:aa:bb:cc")
```

The following fields come defined with the library:

* `Boolean`
* `MulticastGroupId`
* `MulticastNodeId`
* `DevPort`
* `VlanID`
* `EgressSpec`
* `PortId`
* `DigestType`
* `ReplicationId`

### Specifying Custom Fields

If the field is a fixed sized integer or bit sequence, creating a new field is
easy. As an example, a Tofino device port id can be defined as follows:

```python
class PortId(Field):
    bitwidth = 9
```

The (de)serialisation functions are the object method `get_data_bits` and the
class method `from_data_bits`.

More complicated serialisation routines may require custom code. The
`IPv4Address` is defined as follows:

```python
class IPv4Address(Field):
    bitwidth = 32

    def get_data_bits(self):
        return encode_number(int(ipaddress.ip_address(self.value)), self.bitwidth)

    @classmethod
    def from_data_bits(cls, data):
        return cls(ipaddress.ip_address(data).__str__())
```

## Match Types

In the case of key fields, these are qualified by their match type. So far
`LongestPrefixMatch` (LPM), `Ternary` and `Exact` are defined. These match types
encapsulate the field to which they refer. This was a design decision to have 
generic field objects decoupled from whether or not they were part of a key.



### Exact

This match type is exactly what it says on the tin. It will match and only match
exactly the field value which it encapsulates.

Example:

```python
mac_exact = Exact(match=MacAddress('ff:ff:ff:ff:ff:ff'))
```

### Longest Prefix Match

A longest prefix match is where a field has a value and a number representing 
the number of leading bits the match engine is to consider. The "longest" part
means that, when considering a match, the engine will select the most specific
value, i.e, the field with the largest amount of matching leading bits.

If we consider LPM within the context of an IP address, we could consider the
case of two fields which overlap each other:

1. `192.168.16.0/24`
2. `192.168.0.0/16`

> Since any value beyond the prefix will not be considered in the match, it
> doesn't matter what their values are, and convention is to set them to zero.

An address of `192.168.0.1` will match the second rule, and `192.168.16.57`
would match the first.

Since the gRPC message for an LPM contain both the value and the prefix, no
special processing is required other than to select the correct object in any
request and populate it's fields.

Example:

```python
ipv4_lpm = LongestPrefixMatch(match=IPv4Address('192.168.0.0'), prefix=24)
```

### Ternary

Ternary fields match on a value and a mask. The mask bits indicate to the engine
which bits are to be considered.

The mask is specified as value with the exact type of the match value.

In the following example, only the first and third octets are considered in the
match.

Example:

```python
ipv4_ternary = Ternary(match=IPv4Address('192.168.0.1'), mask=IPv4Address('255.0.255.0'))
```

## Acknowledgements

This library makes use of code from and is inspired by
[Simple P4 Client](https://github.com/CommitThis/simplep4client).

This in turn is inspired by code from [P4 Tutorial](https://github.com/p4lang/tutorials)

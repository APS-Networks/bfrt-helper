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



## Acknowledgements

This library makes use of code from and is inspired by
[Simple P4 Client](https://github.com/CommitThis/simplep4client).

This in turn is inspired by code from [P4 Tutorial](https://github.com/p4lang/tutorials)
'''    Copyright 2021 APS Networks GmbH, CommitThis

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

from enum import Enum
import json
import math
import ipaddress


class ValueOutOfRange(Exception):
    pass


def encode_number(number, bitwidth):
    if number >= 2 ** bitwidth:
        raise ValueOutOfRange('Value {} has more bits than {}'.format(number, bitwidth))
    byte_len = int(math.ceil(bitwidth / 8.0))
    num_str = '%x' % number
    num_str = '0' * (byte_len * 2 - len(num_str)) + num_str
    return bytes(bytearray.fromhex(num_str))

def quoted(value):
    if isinstance(value, str):# or isinstance(value, unicode):
        return '\'{}\''.format(value)
    else:
        return value


class P4BaseObject:
    def __repr__(self):
        pairs = [ 
            f'{key}={repr(value)}' for key, value in
                self.__dict__.items() if key != 'bitwidth'
            ]
        return '{}({})'.format(self.__class__.__name__, ', '.join(pairs))


class Field(P4BaseObject):
    def __new__(cls, *args, **kwargs):
        instance = super(Field, cls).__new__(cls)
        instance.bitwidth = cls.bitwidth
        return instance

    def __init__(self, value):
        self.value = value

    def get_data_bits(self):
        return encode_number(self.value, self.bitwidth)

    @classmethod
    def from_data_bits(cls, data):
        return cls(int.from_bytes(data, 'big'))

    def __str__(self):
        if isinstance(self.value, str):
            return '\'' + self.value + '\''
        return str(self.value)


class Match(P4BaseObject):
    def get_data_bits(self):
        return self.match.get_data_bits()

class Exact(Match):
    def __init__(self, match):
        self.match = match


class LongestPrefixMatch(Match):
    def __init__(self, match: Field, prefix: int):
        self.match = match
        self.prefix = prefix

    ''' Probably doesn't need to be a function, but is so for consistency '''
    def get_prefix(self):
        return self.prefix



class Ternary(Match):
    ''' Ternary Match
    If no mask is specified, a mask is generated from the type and bitwidth of
    the value, set to all ones. If the `dont_care` flag is specified, the mask
    will contain all zeroes.
    '''
    def __init__(self, match: Field, mask: Field=None, dont_care=False):
        self.match = match
        self.mask = mask

        if self.mask == None:
            required_bytes =  (match.bitwidth + 7) // 8
            if dont_care:
                mask_bytes = bytearray(required_bytes)
                self.mask = self.match.__class__.from_data_bits(mask_bytes)
            else:
                mask_int = (1 << match.bitwidth) - 1
                mask_bytes = mask_int.to_bytes(required_bytes, 'big')
                self.mask = self.match.__class__.from_data_bits(mask_bytes)

    def get_mask_bits(self):
        return self.mask.get_data_bits()



class MacAddress(Field):
    bitwidth = 48

    def get_data_bits(self):
        return bytes(bytearray.fromhex(self.value.replace(':', '')))

    @classmethod
    def from_data_bits(cls, data):
        return MacAddress(':'.join(['{:02x}'.format(x) for x in data]))


class IPv4Address(Field):
    bitwidth = 32

    def get_data_bits(self):
        return encode_number(int(ipaddress.ip_address(self.value)), self.bitwidth)

    @classmethod
    def from_data_bits(cls, data):
        return cls(ipaddress.ip_address(data).__str__())
 

class Boolean(Field):
    bitwidth = 1

    @classmethod
    def from_data_bits(cls, data):
        int_val = int.from_bytes(data, 'big')
        if not (int_val == 0 or int_val == 1):
            raise Exception(f'Bad value for deserialising boolean: {int_val}')
        return cls(int_val == 1)

TRUE = Boolean(True)
FALSE = Boolean(False)


class MulticastGroupId(Field):
    bitwidth = 16

class MulticastNodeId(Field):
    bitwidth = 32

class DevPort(Field):
    bitwidth = 32

class VlanID(Field):
    bitwidth = 12

class EgressSpec(Field):
    bitwidth = 9

class PortId(Field):
    bitwidth = 9

class DigestType(Field):
    bitwidth = 3

class ReplicationId(Field):
    bitwidth = 16



if __name__ == '__main__':
    match = Ternary(
        match=MacAddress('ff:ff:ff:ff:ff:ff'),
        mask=MacAddress('ff:ff:ff:ff:ff:ff'))
    print(match.get_data_bits())
    print(match.get_mask_bits())
    print(match)


    mac1 = MacAddress('ab:cd:ef:12:34:45')
    mac2 = MacAddress.from_data_bits(mac1.get_data_bits())
    print(repr(mac1))
    print(mac1)
    print(mac2)

    match = Exact(match=MacAddress('ff:ff:ff:ff:ff:ff'))
    print(match)
    print(repr(match))
    print(match.get_data_bits())


    match = LongestPrefixMatch(match=MacAddress('ff:ff:ff:ff:ff:ff'), prefix=24)
    print(match)
    print(repr(match))
    print(match.get_data_bits())


    ip1 = IPv4Address('192.168.0.1')
    ip2 = IPv4Address.from_data_bits(ip1.get_data_bits())
    print(repr(ip1))
    print(ip1.get_data_bits())
    print(ip1)
    print(ip2)


    match = LongestPrefixMatch(match=IPv4Address('192.168.0.1'), prefix=24)
    print(match)
    print(repr(match))
    print(match.get_data_bits())
    print(match.get_prefix())

    match = Ternary(
        match=IPv4Address('192.168.0.1'),
        mask=IPv4Address('255.0.255.0'))
    print(match)
    print(repr(match))
    print(match.get_data_bits())
    print(match.get_mask_bits())


    match = Ternary(match=IPv4Address('192.168.0.1'))
    print(match)
    print(repr(match))
    print(match.get_data_bits())
    print(match.get_mask_bits())


    rid = ReplicationId(42)
    print(rid)
    print(rid.get_data_bits())

    rid = ReplicationId.from_data_bits(rid.get_data_bits())
    print(rid)
    print(rid.get_data_bits())

    print('---- TRUE')
    true = TRUE
    print(true)
    print(repr(true))
    print(true.get_data_bits())
    true = Boolean.from_data_bits(true.get_data_bits())
    print(true)
    print(true.get_data_bits())

    print('---- FALSE')
    false = FALSE
    print(false)
    print(repr(false))
    print(false.get_data_bits())
    false = Boolean.from_data_bits(false.get_data_bits())
    print(false)
    print(false.get_data_bits())

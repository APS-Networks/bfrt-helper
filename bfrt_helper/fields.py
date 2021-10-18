#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Fields
'''

import ipaddress
import math

from bfrt_helper.util import InvalidValue
from bfrt_helper.util import InvalidOperation
from bfrt_helper.util import encode_number



class Field:

    # Make immutable
    __slots__ = []

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        if hasattr(cls, 'bitwidth'):
            instance.bitwidth = cls.bitwidth
        return instance

    def to_bytes(self):
        return encode_number(self.value, self.bitwidth)

    @classmethod
    def from_bytes(cls, data):
        return cls(int.from_bytes(data, 'big'))

    @classmethod
    def max_value(cls):
        return 2 ** cls.bitwidth - 1

    def __init__(self, value=0):
        if hasattr(self, 'bitwidth'):
            max_value = self.__class__.max_value()
            if value > max_value:
                msg = f'Value {value} is greater than the maximum allowed for this '
                msg += f' field. [max={max_value}, bitwidth={self.bitwidth}]'
                raise InvalidValue(msg)
        self.value = value

    def __str__(self):
        if isinstance(self.value, str):
            return f'\'{self.value}\''
        return str(self.value)


    def __repr__(self):
        return f'{self.__class__.__qualname__}({str(self)})'

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.value == other.value

    def __and__(self, other):
        cls = self.__class__
        return cls(self.value & other.value)

    def __or__(self, other):
        cls = self.__class__
        return cls(self.value | other.value)

    def __xor__(self, other):
        cls = self.__class__
        return cls(self.value ^ other.value)



    def __hash__(self):
        return hash(self.value)




''' For data parameters, this may not even be necessary as the class will accept
    a string directly'''
class StringField(Field):

    def __and__(self, other):
        raise InvalidOperation(StringField.invalidop('__and__'))

    def __or__(self, other):
        raise InvalidOperation(StringField.invalidop('__or__'))

    def __xor__(self, other):
        raise InvalidOperation(StringField.invalidop('__xor__'))

    @classmethod
    def max_value(cls):
        raise InvalidOperation(StringField.invalidop('max_value'))

    @staticmethod
    def invalidop(op):
        return f'{op} is not allowed for StringField'

    def to_bytes(self):
        raise NotImplemented()

    @classmethod
    def from_bytes(cls, data):
        raise NotImplemented()




class IPv4Address(Field):
    bitwidth = 32

    def __init__(self, address: str):
        super().__init__(int(ipaddress.ip_address(address)))

    def __str__(self):
        return str(ipaddress.ip_address(self.value))

    ''' Overloaded cause of quotes'''
    def __repr__(self):
        return f'IPv4Address(\'{str(self)}\')'

    @classmethod
    def from_bytes(cls, data):
        return cls(ipaddress.ip_address(data).__str__())




class MACAddress(Field):
    bitwidth = 48

    def __init__(self, address):
        if isinstance(address, int):
             super().__init__(address)
        else:
            super().__init__(int(address.replace(':',''), 16))

    def __str__(self):
        return ':'.join([f'{b:02x}' for b in self.value.to_bytes(6, 16)])

    # def __repr__(self):
    #     return f'MACAddress(\'{str(self)}\')'

    @classmethod
    def from_bytes(cls, data):
        return cls(':'.join([f'{b:02x}' for b in data.to_bytes(6, 16)]))







class PortId(Field):
    bitwidth = 9




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


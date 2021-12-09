import math


_ = None


class InvalidValue(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidOperation(Exception):
    def __init__(self, message):
        super().__init__(message)


class ValueOutOfRange(Exception):
    def __init__(self, message):
        super().__init__(message)


class MatchHelper:
    def __init__(self, *types):
        self.types = tuple(types)

    def create(self, *args):
        for t, arg in zip(args, self.types):
            match_type, field = t
            pass



BYTE_WIDTH = 8

def encode_number(number, bitwidth):
    '''Convert an integer to it's representation in bytes.
    
    gRPC operations involving values are always sent as ``bytes``. Since
    operations internally to the helpers are performed on integers (it is way
    easier), values need to be 'casted' to bytes.

    The byte string will always be the smallest number of bytes capable of
    holding the value based upon the bitwidth. If a value is provided that is
    out of range, an exception will be thrown.

    The number of bytes is calculated as:

    .. math::

        [ (b + 8 - 1) / b ]

    Where :math:`b` is the bitwidth.

    Conversion to bytes is performed via the ``int.to_bytes`` method, using a
    big endian conversion.

    Args:
        number (int): Value to convert
        bitwidth (int): Bitwidth of the field

    Raises:
        ValueOutOfRange: The supplied value exceeds the maximum number the
            bitwidth is capable of supporting.
    '''
    if number >= 2 ** bitwidth:
        raise ValueOutOfRange("Value {} has more bits than {}".format(number,
            bitwidth))
    n_bytes = (bitwidth + BYTE_WIDTH - 1) // BYTE_WIDTH
    return number.to_bytes(n_bytes, 'big')


def bit_not(value, n_bits):
    '''Calculates the bitwise negation (NOT) of an integer.
    
    Since integers in python are both signed and have arbitrary lengths,
    calculating the bitwsie negation is not straightforward.

    The is calculated by:
    
    .. math::
    
            (2^b-1) - x
            
    Where :math:`b` is the number of bits in the value and :math:`x` is the
    value to convert.

    Note:
        This will not work on negative numbers.

    Args:
        value (int): The value to convert.
        n_bits (int): The number of bits the value should have.

    '''
    return (1 << n_bits) - 1 - value


def mask_from_prefix(bitwidth, prefix):
    '''Calculates a mask for the given bitwidth and prefix.
    
    .. math::

        2^{p-1} \ll (w - p)

    '''
    return (2 ** prefix - 1) << (bitwidth - prefix)



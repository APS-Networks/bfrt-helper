_ = None




class MatchHelper:
    def __init__(self, *types):
        self.types = tuple(types)

    def create(self, *args):
        for t, arg in zip(args, self.types):
            match_type, field = t
            pass

import math




def encode_number(number, bitwidth):
    if number >= 2 ** bitwidth:
        raise ValueOutOfRange('Value {} has more bits than {}'.format(number, bitwidth))
    byte_len = int(math.ceil(bitwidth / 8.0))
    num_str = f'{number:x}'
    # num_str = '%x' % number
    num_str = '0' * (byte_len * 2 - len(num_str)) + num_str
    return bytes(bytearray.fromhex(num_str))




def bit_not(value, b_bits):
    return (1 << n_bits) - 1 - value




class InvalidValue(Exception):
    def __init__(self, message):
        super().__init__(message)




class InvalidOperation(Exception):
    def __init__(self, message):
        super().__init__(message)



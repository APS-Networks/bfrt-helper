from bfrt_helper.util import InvalidOperation
from bfrt_helper.util import InvalidValue
from bfrt_helper.util import mask_from_prefix
from bfrt_helper.fields import Field
from bfrt_helper.fields import IPv4Address


class MismatchedKeys(Exception):
    def __init__(self, message):
        super().__init__(message)


class MismatchedTypes(Exception):
    def __init__(self, message):
        super().__init__(message)


class Masked:
    def __init__(self):
        self.value = None
        self.mask = None

    def subset_of(self, other) -> bool:
        if not self.mask & other.mask == other.mask:
            return False
        return (self.value & other.mask) == (other.value & other.mask)

    def superset_of(self, other) -> bool:
        if not self.mask & other.mask == self.mask:
            return False
        return (self.value & self.mask) == (other.value & self.mask)

    def intersection(self, other):
        return self.__class__(
            value=self.value | other.value,
            mask=self.mask | other.mask)

    def union(self, other):
        new_mask = self.mask & other.mask
        return self.__class__(self.value & new_mask, new_mask)

    def overlaps(self, other) -> bool:
        c_mask = self.mask & other.mask
        return not (c_mask == self.mask or c_mask == other.mask) and (
            self.value & c_mask == other.value & c_mask
        )

    def __hash__(self):
        return hash((self.value, self.mask))

    def __le__(self, other) -> bool:
        return self.subset_of(other)

    def __ge__(self, other) -> bool:
        return self.superset_of(other)

    def __lt__(self, other):
        return self.subset_of(other) and not self == other

    def __gt__(self, other):
        return self.superset_of(other) and not self == other

    def __eq__(self, other) -> bool:
        return (self.value == other.value) & (self.mask == other.mask)

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def __iter__(self):
        def iterator(ternary):
            global_max_value = (1 << self.value.bitwidth) - 1
            local_max_val = global_max_value - self.mask.value
            local_max_val = self.value.value | local_max_val
            temp = self.value.value

            match_cls = self.__class__
            value_cls = self.value.__class__
            yield match_cls(value_cls(temp), value_cls(global_max_value))

            initial = self.value.value
            mask = self.mask.value
            while temp < local_max_val:
                temp += 1
                if temp & mask != initial:
                    continue
                if temp & initial != temp:
                    yield match_cls(value_cls(temp), value_cls(global_max_value))

        return iterator(self)


class Ternary(Masked):
    def __init__(self, value: Field, mask: Field = None, dont_care=False):
        super().__init__()

        self.max_value = (2 ** value.bitwidth) - 1
        self.value = value
        self.mask = mask

        if mask is None:
            required_bytes = (value.bitwidth + 7) // 8
            if dont_care:
                mask_int = 0
                mask_bytes = mask_int.to_bytes(required_bytes, "big")
                mask = value.__class__.from_bytes(mask_bytes)
            else:
                mask_int = (1 << value.bitwidth) - 1
                mask_bytes = mask_int.to_bytes(required_bytes, "big")
                mask = value.__class__.from_bytes(mask_bytes)
        elif not isinstance(mask, value.__class__):
            mask = value.__class__(mask)

        self.value = value & mask
        self.mask = mask

    def value_bytes(self):
        return self.value.to_bytes()

    def mask_bytes(self):
        return self.mask.to_bytes()

    @classmethod
    def dont_care(self):
        pass

    def __str__(self):
        if self.mask.value == self.max_value:
            return str(self.value)
        return f"{str(self.value)} &&& {str(self.mask)}"

    def __repr__(self):
        return f"Ternary({repr(self.value)}, mask={repr(self.mask)})"


class LPM(Masked):
    def __init__(self, value: Field, prefix: int):
        super().__init__()

        if prefix > value.bitwidth:
            msg = f"Prefix {prefix} is greater than the maximum allowed for this "
            msg += f" field. [bitwidth={value.bitwidth}]"
            raise InvalidValue(msg)
        self.mask = value.__class__((2 ** prefix - 1) << (value.bitwidth - prefix))
        self.value = value & self.mask
        self.prefix = prefix

    def __str__(self):
        return f"{self.value}/{self.prefix}"

    def __repr__(self):
        return f"LPM({repr(self.value)}, prefix={self.prefix})"

    def value_bytes(self):
        return self.value.to_bytes()


class Exact:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def value_bytes(self):
        return self.value.to_bytes()


class Match:
    def __init__(self, **fields):
        self.fields = fields

    def __gt__(self, other):
        return self.superset_of(other) and not self == other

    def __lt__(self, other):
        return self.subset_of(other) and not self == other

    def __ge__(self, other):
        return self.superset_of(other)

    def __le__(self, other):
        return self.subset_of(other)

    def __eq__(self, other):
        return self.equal_(other)

    def __hash__(self):
        return hash((*self.fields.keys(), *self.fields.values()))

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def __equality_check(self, other):
        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if k1 != k2:
                raise MismatchedKeys(f'Key {k1} is not equal to {k2}')
            if type(v1) != type(v2):
                raise MismatchedTypes(f'Type of {v1} ({type(v1)}) is not equal to {v2} ({type(v2)})')

    def conflicts(self, other):
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1.conflicts(v2)
            else:
                acc = acc and v1 == v2
        return acc

    def intersection(self, other):
        args = {}

        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if isinstance(v1, Ternary):
                # args.append(v1.intersection(v2))
                args[k1] = v1.intersection(v2)
            elif isinstance(v1, LPM):
                # args.append(LPM(v1.value | v2.value, max(v1.prefix, v2.prefix)))
                args[k1] = LPM(v1.value | v2.value, max(v1.prefix, v2.prefix))
            else:
                if v1 != v2:
                    raise InvalidOperation(
                        "Trying to calculate the difference "
                        + "on matches containing non-equal exact values."
                    )
                args[k1] = v1
        return Match(**args)

    def superset_of(self, other):
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 >= v2
            else:
                acc = acc and v1 == v2
        return acc

    def subset_of(self, other):
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 <= v2
            else:
                acc = acc and v1 == v2
        return acc

    def proper_superset_of(self, other):
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 > v2
            else:
                acc = acc and v1 == v2
        return acc

    def proper_subset_of(self, other):
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and v1 < v2
            else:
                acc = acc and v1 == v2
        return acc
        # return acc

    def equal_(self, other):
        acc = True
        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            acc = acc and v1 == v2
        return acc

    def overlaps(self, other):
        acc = True

        if self < other:
            return False
        if self > other:
            return False
        if self == other:
            return False

        self.__equality_check(other)

        for (k1, v1), (k2, v2) in zip(
                self.fields.items(), 
                other.fields.items()):

            if isinstance(v1, Masked):
                acc = acc and (v1 >= v2 or v1 <= v2 or v1.overlaps(v2))
            else:
                acc = acc and v1 == v2
        return acc

    def __str__(self):
        field_strings = []
        for k, v in self.fields.items():
            if isinstance(v, Ternary):
                if v.mask.value == 0:
                    field_strings.append("_")
                else:
                    field_strings.append(str(v))
            else:
                field_strings.append(str(v))
        return "{{  {}  }}".format(", ".join(field_strings))

    def __repr__(self):
        acc = 'Match('
        acc += ', '.join([f'"{k}={repr(v)}"' for k, v in self.fields.items()])
        return acc + ')'


class IPv4AddressTernary(Ternary):
    ''' The asterisk captures all positional parameters, forcing everything to
        be named '''
    def __init__(self, value, *, prefix=None, mask=None, dont_care=False):
        if not isinstance(value, IPv4Address):
            value = IPv4Address(value)
        if prefix:
            mask = IPv4Address(mask_from_prefix(IPv4Address.bitwidth, prefix))

        super().__init__(value, mask, dont_care)
